import { h } from "../dom.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { messageOf, messageSlot, notice } from "../ui/feedback.js";
import { whileBusy } from "../ui/forms.js";
import { linkButton } from "../ui/layout.js";

// The panel that asks what a person wants to do: start a group as the mother or as a partner, or
// wait for a link. It is the start screen of a person without a group and the "Dodaj grupę"
// dialog of a person who has some. The mother choice is offered only to a person who is not yet
// the mother of a group. `onStarted` runs after a group was created and selected.
export function groupPanel(ctx, { onStarted } = {}) {
  const message = messageSlot();
  const waiting = h("div", { class: "panel__waiting" });

  function choice(iconName, title, text, action) {
    const node = h(
      "button",
      { class: "start-choice", type: "button" },
      h("span", { class: "icon-badge" }, icon(iconName)),
      h(
        "span",
        { class: "start-choice__text" },
        h("span", { class: "start-choice__title" }, title),
        h("span", { class: "start-choice__lead" }, text),
      ),
      icon("arrow"),
    );
    node.addEventListener("click", () =>
      whileBusy(node, async () => {
        message.clear();
        waiting.replaceChildren();
        try {
          await action();
        } catch (error) {
          message.error(messageOf(error));
        }
      }),
    );
    return h("li", {}, node);
  }

  const startAs = (role) => async () => {
    const created = await ctx.api.call("create_group", { body: { role } });
    await ctx.enterGroup(created.id);
    if (onStarted) onStarted();
    ctx.navigate("/");
  };

  const showWaiting = async () => {
    waiting.replaceChildren(
      notice(
        { iconName: "link" },
        h("strong", {}, t.group.waitForLinkTitle),
        t.group.waitForLinkText,
        t.group.waitForLinkMore,
      ),
      h(
        "div",
        { class: "actions" },
        linkButton("#/education", t.nav.education, { variant: "ghost", iconName: "book" }),
        linkButton("#/help", t.nav.help, { variant: "ghost", iconName: "lifebuoy" }),
      ),
    );
  };

  return h(
    "div",
    { class: "panel stack" },
    message.node,
    h(
      "ul",
      { class: "start-choices" },
      !ctx.session.hasWomanGroup &&
        choice("heart", t.group.asMother, t.group.asMotherText, startAs("woman")),
      choice("people", t.group.asPartner, t.group.asPartnerText, startAs("partner")),
      choice("link", t.group.asWaiting, t.group.asWaitingText, showWaiting),
    ),
    waiting,
  );
}
