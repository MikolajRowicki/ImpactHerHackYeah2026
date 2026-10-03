import { h } from "../dom.js";
import { icon, SELF_CARE_ICONS } from "../icons.js";
import { t } from "../strings.pl.js";
import { linkButton, pageHead, section } from "../ui/layout.js";
import { summaryCard } from "../ui/summary.js";
import { onboarding, waiting } from "./onboarding.js";
import { tasksPreview } from "./tasks-preview.js";

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

function ctaCard(href, iconName, title, lead) {
  return h(
    "a",
    { class: "cta-card", href },
    h("span", { class: "icon-badge" }, icon(iconName, 26)),
    h(
      "span",
      { class: "cta-card__text" },
      h("span", { class: "cta-card__title" }, title),
      h("span", { class: "cta-card__lead" }, lead),
    ),
    icon("arrow"),
  );
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

function selfCare(items) {
  return section(
    { title: t.wellbeing.selfCareTitle, id: "self-care-title" },
    h(
      "ul",
      { class: "self-care" },
      ...items.map((item) =>
        h(
          "li",
          { class: "card self-care__item" },
          h("span", { class: "icon-badge" }, icon(SELF_CARE_ICONS[item.kind] || "sparkle")),
          h(
            "div",
            { class: "self-care__text" },
            h(
              "h3",
              { class: "self-care__title" },
              item.title,
              h(
                "span",
                { class: "chip" },
                icon("clock", 14),
                t.wellbeing.minutes(item.duration_minutes),
              ),
            ),
            h("p", {}, item.description),
          ),
        ),
      ),
    ),
  );
}

async function motherStart(ctx) {
  const [summary, members, care, tasks] = await Promise.all([
    ctx.api.call("get_summary"),
    ctx.api.call("list_members"),
    ctx.api.call("list_self_care"),
    ctx.api.call("list_tasks"),
  ]);
  const active = ctx.session.groupStatus === "active";
  const alone = members.items.length < 2 && active;
  const node = h(
    "div",
    { class: "mother-start" },
    greeting(ctx),
    h(
      "div",
      { class: "start-grid" },
      h(
        "div",
        { class: "start-grid__main stack-large" },
        active && ctaCard("#/check-in", "leaf", t.wellbeing.ctaTitle, t.wellbeing.ctaLead),
        alone && invitePartnerCard(),
        summaryCard(summary),
      ),
      h(
        "div",
        { class: "start-grid__side" },
        selfCare(care.items),
        tasksPreview(tasks.items, { title: t.wellbeing.tasksTitle, empty: t.wellbeing.tasksEmpty }),
      ),
    ),
  );
  node.dataset.wide = "true";
  return node;
}

async function lovedStart(ctx) {
  const summary = await ctx.api.call("get_summary");
  return h("div", { class: "stack-large" }, greeting(ctx), summaryCard(summary));
}
