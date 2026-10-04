import { h } from "../dom.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { originLabel } from "../ui/ai.js";
import { crisisLines } from "../ui/crisis-lines.js";
import { messageOf, notice } from "../ui/feedback.js";
import { choiceGroup, field, showFieldErrors, submitButton, whileBusy } from "../ui/forms.js";
import { button, linkButton, pageHead } from "../ui/layout.js";

const MAX_LENGTH = 500;

function options(labels) {
  return Object.entries(labels).map(([value, label]) => ({ value, label }));
}

function focusHeading(container) {
  container.querySelector("h2")?.focus();
}

// The mother writes what is hard to say and gets a message she can edit and copy.
// Her text lives only in this form: it is not stored, here or anywhere else.
export async function sayIt(ctx) {
  const text = field({
    label: t.sayIt.text,
    name: "text",
    hint: t.sayIt.textHint,
    maxlength: MAX_LENGTH,
    multiline: true,
  });
  text.input.rows = 5;
  text.input.setAttribute("autocomplete", "off");
  const counter = h(
    "p",
    { class: "say-it__counter", id: `${text.input.id}-counter` },
    t.sayIt.counter(0, MAX_LENGTH),
  );
  text.input.setAttribute(
    "aria-describedby",
    `${text.input.getAttribute("aria-describedby")} ${counter.id}`,
  );
  // Inside the field, right under the text, so it never overlaps the box.
  text.input.after(counter);
  text.input.addEventListener("input", () => {
    counter.textContent = t.sayIt.counter(text.value.length, MAX_LENGTH);
    if (text.value.trim()) text.setError("");
  });
  const recipient = choiceGroup({
    legend: t.sayIt.recipient,
    name: "recipient",
    options: options(t.sayIt.recipients),
    value: "partner",
  });
  const tone = choiceGroup({
    legend: t.sayIt.tone,
    name: "tone",
    options: options(t.sayIt.tones),
    value: "gentle",
  });
  const submit = submitButton(t.sayIt.send, { variant: "accent", iconName: "sparkle" });
  const form = h(
    "form",
    { class: "form say-it-form", novalidate: true },
    text.node,
    recipient.node,
    tone.node,
    submit,
  );
  const result = h("div", { class: "say-it__result" });
  let lastBody = null;
  // Only the answer to the latest request may be shown: a slow, older answer must never
  // replace a newer one, above all not a crisis answer.
  let latest = 0;

  async function send(body, trigger) {
    await whileBusy(
      trigger,
      async () => {
        // Counted only when a request really leaves: a press on a busy button sends nothing.
        lastBody = body;
        const ticket = ++latest;
        try {
          const answer = await ctx.api.call("ai_say_it_for_me", { body });
          if (ticket !== latest) return;
          result.replaceChildren(answer.crisis ? crisisCard(answer) : messageCard(answer));
          focusHeading(result);
        } catch (error) {
          if (ticket !== latest) return;
          result.replaceChildren();
          if (error.status === 422 && showFieldErrors(error, { text, recipient, tone })) {
            text.input.focus();
            return;
          }
          result.replaceChildren(failure(error));
          // The pressed button was disabled and lost the focus; the way out gets it.
          result.querySelector("button")?.focus();
        }
      },
      { label: t.ai.preparing },
    );
  }

  function messageCard(answer) {
    // Tall enough for the whole message on a phone (about 34 characters a line).
    const rows = Math.min(14, Math.max(6, Math.ceil(answer.message.length / 34) + 1));
    const message = h("textarea", {
      id: "say-it-message",
      class: "field__input say-it__message",
      rows,
    });
    message.value = answer.message;
    const status = h("p", { class: "say-it__copied", role: "status" });
    const copy = button(t.sayIt.copy, {
      variant: "accent",
      iconName: "copy",
      async onclick() {
        try {
          await navigator.clipboard.writeText(message.value);
          status.textContent = t.sayIt.copied;
        } catch {
          // No clipboard (an old browser or a refused permission): select it for a manual copy.
          message.focus();
          message.select();
          status.textContent = t.sayIt.copyFailed;
        }
      },
    });
    const again = button(t.sayIt.again, {
      variant: "ghost",
      iconName: "sparkle",
      onclick: () => send(lastBody, again),
    });
    return h(
      "section",
      { class: "card say-it__card stack", "aria-labelledby": "say-it-result-title" },
      h(
        "h2",
        { id: "say-it-result-title", class: "card__title", tabindex: "-1" },
        t.sayIt.resultTitle,
      ),
      originLabel(answer),
      h("label", { class: "field__label", for: message.id }, t.sayIt.message),
      message,
      h("div", { class: "actions" }, copy, again),
      status,
    );
  }

  function crisisCard(answer) {
    return h(
      "section",
      { class: "card card--accent say-it__crisis stack", "aria-labelledby": "say-it-crisis-title" },
      h(
        "h2",
        { id: "say-it-crisis-title", class: "card__title", tabindex: "-1" },
        icon("heart"),
        t.sayIt.crisisTitle,
      ),
      h("p", {}, t.sayIt.crisisText),
      crisisLines(answer.help?.crisis_lines || []),
      h(
        "div",
        { class: "actions" },
        linkButton("#/help", t.sayIt.crisisHelp, { iconName: "lifebuoy" }),
      ),
    );
  }

  function failure(error) {
    const retry = button(t.common.retry, {
      iconName: "arrow",
      onclick: () => send(lastBody, retry),
    });
    return h(
      "div",
      { class: "stack" },
      notice({ tone: "error", role: "alert" }, messageOf(error, t.sayIt.failed)),
      h("div", { class: "actions" }, retry),
    );
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const value = text.value.trim();
    text.setError(value ? "" : t.sayIt.textMissing);
    if (!value) {
      text.input.focus();
      return;
    }
    await send({ text: value, recipient: recipient.value, tone: tone.value }, submit);
  });

  return h(
    "div",
    { class: "say-it stack-large" },
    pageHead({
      title: t.sayIt.title,
      eyebrow: t.sayIt.eyebrow,
      eyebrowIcon: "feather",
      lead: t.sayIt.lead,
    }),
    notice({ iconName: "lock" }, t.sayIt.privacy),
    h("div", { class: "card" }, form),
    result,
  );
}
