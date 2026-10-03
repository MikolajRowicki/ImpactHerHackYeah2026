import { h } from "../dom.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { messageOf, messageSlot, notice } from "../ui/feedback.js";
import { whileBusy } from "../ui/forms.js";
import { pageHead, section } from "../ui/layout.js";
import { invitationForm } from "./invitation-form.js";

// Start for a signed-in person without a group: start one, or join with a link.
export async function onboarding(ctx) {
  const message = messageSlot();

  function startButton(role, iconName, title, text) {
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
        try {
          await ctx.api.call("create_group", { body: { role } });
          await ctx.reloadSession();
          ctx.navigate("/");
        } catch (error) {
          message.error(messageOf(error));
        }
      }),
    );
    return h("li", {}, node);
  }

  return h(
    "div",
    { class: "onboarding" },
    pageHead({
      title: t.start.greeting(ctx.session.me.display_name),
      lead: t.group.onboardingLead,
    }),
    message.node,
    section(
      { title: t.group.startAsTitle, id: "start-as-title" },
      h(
        "ul",
        { class: "start-choices" },
        startButton("woman", "heart", t.group.asMother, t.group.asMotherText),
        startButton("partner", "people", t.group.asPartner, t.group.asPartnerText),
      ),
    ),
    section(
      { title: t.group.joinTitle, id: "join-title" },
      notice({ iconName: "link" }, t.group.joinText),
    ),
  );
}

// Start for a member of a pending group: the explanation and, for the partner, the invitation.
export async function waiting(ctx) {
  const isPartner = ctx.session.role === "partner";
  return h(
    "div",
    { class: "waiting" },
    pageHead({
      title: t.group.waitingTitle,
      eyebrow: t.start.greeting(ctx.session.me.display_name),
      eyebrowIcon: "clock",
      lead: t.group.waitingLead,
    }),
    h("p", { class: "muted" }, t.group.waitingText),
    isPartner &&
      section(
        { title: t.group.inviteMotherTitle, id: "invite-mother-title" },
        h("div", { class: "card" }, h("p", {}, t.group.inviteMotherText), invitationForm(ctx, ["woman"])),
      ),
  );
}
