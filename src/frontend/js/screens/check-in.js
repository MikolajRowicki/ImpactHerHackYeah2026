import { h } from "../dom.js";
import { dayAndTime } from "../format.js";
import { t } from "../strings.pl.js";
import { emptyState, messageOf, messageSlot, notice } from "../ui/feedback.js";
import { choiceGroup, submitButton, whileBusy } from "../ui/forms.js";
import { pageHead, section } from "../ui/layout.js";

const QUESTIONS = ["mood", "sleep", "anxiety"];

function options(name) {
  return Object.entries(t.wellbeing[name].options).map(([value, label]) => ({ value, label }));
}

// Her entries in words, newest first. No chart, number or score.
function history(items) {
  if (items.length === 0) return emptyState({ iconName: "leaf", text: t.wellbeing.historyEmpty });
  return h(
    "ol",
    { class: "card-list history" },
    ...items.map((entry) =>
      h(
        "li",
        { class: "card history__entry" },
        h("h3", {}, h("time", { datetime: entry.created_at }, dayAndTime(entry.created_at))),
        h(
          "dl",
          { class: "history__answers" },
          ...QUESTIONS.flatMap((name) => [
            h("dt", {}, t.wellbeing[name].label),
            h("dd", {}, t.wellbeing[name].options[entry[name]] || ""),
          ]),
        ),
      ),
    ),
  );
}

function checkInForm(ctx, onSaved) {
  const message = messageSlot();
  const groups = Object.fromEntries(
    QUESTIONS.map((name) => [
      name,
      choiceGroup({ legend: t.wellbeing[name].legend, name, options: options(name) }),
    ]),
  );
  const submit = submitButton(t.wellbeing.save, { variant: "accent", iconName: "check" });
  const form = h(
    "form",
    { class: "form check-in-form", novalidate: true },
    ...QUESTIONS.map((name) => groups[name].node),
    message.node,
    submit,
  );

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.clear();
    const missing = QUESTIONS.filter((name) => !groups[name].value);
    for (const name of QUESTIONS) {
      groups[name].setError(missing.includes(name) ? t.wellbeing.pickOne : "");
    }
    if (missing.length) {
      groups[missing[0]].focus();
      return;
    }
    const body = Object.fromEntries(QUESTIONS.map((name) => [name, groups[name].value]));
    await whileBusy(submit, async () => {
      try {
        await ctx.api.call("create_check_in", { body });
        await onSaved();
      } catch (error) {
        for (const [name, text] of Object.entries(error.fields || {})) groups[name]?.setError(text);
        message.error(messageOf(error));
      }
    });
  });
  return form;
}

export async function checkIn(ctx) {
  const { items } = await ctx.api.call("list_check_ins");
  const closed = ctx.session.groupStatus === "closed";
  const historyBox = h("div", {}, history(items));
  const formBox = h("div", { class: "card check-in-card" });

  async function onSaved() {
    const fresh = await ctx.api.call("list_check_ins");
    historyBox.replaceChildren(history(fresh.items));
    formBox.replaceChildren(
      notice({ tone: "success", iconName: "heart", role: "status" }, t.wellbeing.saved),
      checkInForm(ctx, onSaved),
    );
  }

  if (closed) formBox.replaceChildren(notice({ tone: "accent", iconName: "lock" }, t.wellbeing.closed));
  else formBox.replaceChildren(checkInForm(ctx, onSaved));

  return h(
    "div",
    { class: "check-in stack-large" },
    pageHead({ title: t.wellbeing.title, eyebrowIcon: "leaf", lead: t.wellbeing.lead }),
    notice({ iconName: "lock" }, t.wellbeing.privacy),
    formBox,
    section({ title: t.wellbeing.historyTitle, id: "history-title" }, historyBox),
  );
}
