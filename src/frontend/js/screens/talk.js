import { h } from "../dom.js";
import { t } from "../strings.pl.js";
import { originLabel, sourcesList } from "../ui/ai.js";
import { messageSlot, notice } from "../ui/feedback.js";
import { whileBusy } from "../ui/forms.js";
import { button, pageHead } from "../ui/layout.js";

const TOPICS = Object.keys(t.talk.topics);

function topicList(current) {
  return h(
    "nav",
    { class: "talk__topics", "aria-label": t.talk.topicsLabel },
    h(
      "ul",
      {},
      ...TOPICS.map((topic) =>
        h(
          "li",
          {},
          h(
            "a",
            {
              class: "talk__topic",
              href: `#/talk/${topic}`,
              "aria-current": topic === current ? "page" : null,
            },
            t.talk.topics[topic],
          ),
        ),
      ),
    ),
  );
}

function part(title, items, id) {
  return h(
    "section",
    { class: "talk__part", "aria-labelledby": id },
    h("h3", { id }, title),
    h("ul", {}, ...items.map((line) => h("li", {}, line))),
  );
}

// A partner or supporter picks a topic and gets opening lines, things to avoid, questions and
// the sources the lines were based on. Each topic has its own address, #/talk/<topic>.
export async function talk(ctx) {
  const topic = ctx.params.topic;
  const head = pageHead({
    title: t.talk.title,
    eyebrow: t.talk.eyebrow,
    eyebrowIcon: "heart",
    lead: t.talk.lead,
  });
  if (!TOPICS.includes(topic)) {
    const hint = topic ? t.talk.unknownTopic : t.talk.pickTopic;
    return h("div", { class: "talk stack-large" }, head, topicList(null), notice({}, hint));
  }

  const guideBox = h("div", {});
  const message = messageSlot();

  function guideCard(answer) {
    const again = button(t.talk.again, {
      variant: "ghost",
      iconName: "sparkle",
      async onclick() {
        message.clear();
        await whileBusy(
          again,
          async () => {
            try {
              const fresh = await ctx.api.call("ai_conversation_guide", { query: { topic } });
              guideBox.replaceChildren(guideCard(fresh));
              guideBox.querySelector("h2")?.focus();
            } catch {
              message.error(t.talk.failed);
            }
          },
          { label: t.ai.preparing },
        );
        // After a failure this card stays and its button lost the focus while disabled.
        if (again.isConnected) again.focus();
      },
    });
    return h(
      "section",
      { class: "card talk__guide stack", "aria-labelledby": "talk-guide-title" },
      h(
        "h2",
        { id: "talk-guide-title", class: "card__title", tabindex: "-1" },
        t.talk.topics[answer.topic] || t.talk.topics[topic],
      ),
      originLabel(answer),
      part(t.talk.openingTitle, answer.opening_lines, "talk-opening"),
      part(t.talk.avoidTitle, answer.avoid, "talk-avoid"),
      part(t.talk.questionsTitle, answer.questions, "talk-questions"),
      h("div", { class: "actions" }, again),
      message.node,
      sourcesList(answer.sources, "talk-sources-title"),
      h("p", { class: "talk__note" }, t.talk.note),
    );
  }

  const answer = await ctx.api.call("ai_conversation_guide", { query: { topic } });
  guideBox.replaceChildren(guideCard(answer));
  return h("div", { class: "talk stack-large" }, head, topicList(topic), guideBox);
}
