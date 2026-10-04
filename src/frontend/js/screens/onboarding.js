import { h } from "../dom.js";
import { t } from "../strings.pl.js";
import { ctaCard, pageHead, section } from "../ui/layout.js";
import { invitationForm } from "./invitation-form.js";
import { groupPanel } from "./panel.js";

// Start for a signed-in person without a group: the panel that asks what they want to do.
export async function onboarding(ctx) {
  return h(
    "div",
    { class: "onboarding" },
    pageHead({
      title: t.start.greeting(ctx.session.me.display_name),
      lead: t.group.onboardingLead,
    }),
    section({ title: t.group.startAsTitle, id: "start-as-title" }, groupPanel(ctx)),
    section(
      { title: t.startGeneral.title, id: "general-title" },
      h(
        "div",
        { class: "stack" },
        ctaCard("#/education", "book", t.startGeneral.educationTitle, t.startGeneral.educationLead),
        ctaCard("#/help", "lifebuoy", t.startGeneral.helpTitle, t.startGeneral.helpLead),
      ),
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
