import { h } from "../dom.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { linkButton, pageHead } from "../ui/layout.js";
import { summaryCard } from "../ui/summary.js";
import { onboarding, waiting } from "./onboarding.js";

// `#/` shows a different start for each situation of the signed-in person.
export async function start(ctx) {
  const membership = ctx.session.me.membership;
  if (!membership) return onboarding(ctx);
  if (membership.group_status === "pending") return waiting(ctx);
  if (membership.role === "woman") return motherStart(ctx);
  return lovedStart(ctx);
}

function greeting(ctx) {
  return pageHead({
    title: t.start.greeting(ctx.session.me.display_name),
    eyebrow: t.common.roles[ctx.session.me.membership?.role],
  });
}

// Shown to the mother while nobody else is in her group yet.
function invitePartnerCard() {
  return h(
    "div",
    { class: "card card--accent invite-offer" },
    h("h2", { class: "card__title" }, icon("people"), t.group.invitePartnerTitle),
    h("p", {}, t.group.invitePartnerText),
    linkButton("#/group", t.group.invitePartnerLink, { iconName: "arrow" }),
  );
}

async function motherStart(ctx) {
  const [summary, members] = await Promise.all([
    ctx.api.call("get_summary"),
    ctx.api.call("list_members"),
  ]);
  const alone = members.items.length < 2 && ctx.session.groupStatus === "active";
  return h(
    "div",
    { class: "stack-large" },
    greeting(ctx),
    alone && invitePartnerCard(),
    summaryCard(summary),
  );
}

async function lovedStart(ctx) {
  const summary = await ctx.api.call("get_summary");
  return h("div", { class: "stack-large" }, greeting(ctx), summaryCard(summary));
}
