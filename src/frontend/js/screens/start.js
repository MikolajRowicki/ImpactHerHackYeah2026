import { h } from "../dom.js";
import { icon, SELF_CARE_ICONS } from "../icons.js";
import { t } from "../strings.pl.js";
import { ctaCard, pageHead, section } from "../ui/layout.js";
import { summaryCard } from "../ui/summary.js";
import { invitationForm } from "./invitation-form.js";
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

// Shown to the mother while nobody else is in her group yet: invite at once, right here.
function inviteAtOnceCard(ctx) {
  return h(
    "section",
    { class: "card card--accent invite-offer", "aria-labelledby": "invite-at-once-title" },
    h(
      "h2",
      { id: "invite-at-once-title", class: "card__title" },
      icon("people"),
      t.group.inviteAtOnceTitle,
    ),
    h("p", {}, t.group.inviteAtOnceText),
    invitationForm(ctx, ["partner", "supporter"]),
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
    ctx.api.call("get_summary_extended"),
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
        alone && inviteAtOnceCard(ctx),
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
  const [summary, tasks] = await Promise.all([
    ctx.api.call("get_summary_extended"),
    ctx.api.call("list_tasks"),
  ]);
  const active = ctx.session.groupStatus === "active";
  const node = h(
    "div",
    { class: "loved-start" },
    greeting(ctx),
    h(
      "div",
      { class: "start-grid" },
      h(
        "div",
        { class: "start-grid__main stack-large" },
        active &&
          ctaCard("#/questions", "chat", t.observations.ctaTitle, t.observations.ctaLead),
        summaryCard(summary),
      ),
      h(
        "div",
        { class: "start-grid__side" },
        tasksPreview(tasks.items, {
          title: t.observations.tasksTitle,
          empty: t.observations.tasksEmpty,
        }),
      ),
    ),
  );
  node.dataset.wide = "true";
  return node;
}
