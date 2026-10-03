import { h } from "../dom.js";
import { t } from "../strings.pl.js";
import { messageOf, messageSlot, notice } from "../ui/feedback.js";
import { choiceGroup, submitButton, whileBusy } from "../ui/forms.js";
import { linkButton, pageHead, stateScreen } from "../ui/layout.js";

// Closed questions about her daily life. Answers are sent once and never shown back.
export async function questions(ctx) {
  const { items } = await ctx.api.call("list_observation_questions");
  const message = messageSlot();
  const groups = items.map((question) => ({
    id: question.id,
    group: choiceGroup({
      legend: question.text,
      name: question.id,
      options: question.answers.map((answer) => ({ value: answer.value, label: answer.label })),
    }),
  }));
  const submit = submitButton(t.observations.send, { variant: "accent", iconName: "check" });
  const form = h(
    "form",
    { class: "form questions-form", novalidate: true },
    ...groups.map(({ group }) => group.node),
    message.node,
    submit,
  );
  const node = h(
    "div",
    { class: "questions stack-large" },
    pageHead({ title: t.observations.title, eyebrowIcon: "chat", lead: t.observations.lead }),
    notice({ iconName: "lock" }, t.observations.privacy),
    h("div", { class: "card" }, form),
  );

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.clear();
    const answers = groups
      .filter(({ group }) => group.value)
      .map(({ id, group }) => ({ question_id: id, value: group.value }));
    if (answers.length === 0) {
      message.error(t.observations.atLeastOne);
      return;
    }
    await whileBusy(submit, async () => {
      try {
        await ctx.api.call("create_observation", { body: { answers } });
      } catch (error) {
        message.error(messageOf(error));
        return;
      }
      // The thank-you replaces the form, so the given answers are gone from the page.
      const thanks = stateScreen({
        iconName: "heart",
        title: t.observations.thanksTitle,
        text: t.observations.thanksText,
        actions: [
          linkButton("#/", t.common.backHome, { iconName: "back", variant: "ghost" }),
          linkButton("#/tasks", t.observations.toTasks, { iconName: "tasks" }),
        ],
      });
      node.replaceWith(thanks);
      const heading = thanks.querySelector("h1");
      heading.setAttribute("tabindex", "-1");
      heading.focus();
    });
  });

  return node;
}
