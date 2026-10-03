import { h } from "../dom.js";
import { t } from "../strings.pl.js";
import { pageHead } from "../ui/layout.js";
import { summaryCard } from "../ui/summary.js";

// `#/` shows a different start for each situation of the signed-in person.
export async function start(ctx) {
  const membership = ctx.session.me.membership;
  if (!membership) return noGroupStart(ctx);
  if (membership.group_status === "pending") return pendingStart(ctx);
  if (membership.role === "woman") return motherStart(ctx);
  return lovedStart(ctx);
}

function greeting(ctx) {
  return pageHead({
    title: t.start.greeting(ctx.session.me.display_name),
    eyebrow: t.common.roles[ctx.session.me.membership?.role],
  });
}

async function noGroupStart(ctx) {
  return h("div", {}, greeting(ctx));
}

async function pendingStart(ctx) {
  return h("div", {}, greeting(ctx));
}

async function motherStart(ctx) {
  const summary = await ctx.api.call("get_summary");
  return h("div", { class: "stack-large" }, greeting(ctx), summaryCard(summary));
}

async function lovedStart(ctx) {
  const summary = await ctx.api.call("get_summary");
  return h("div", { class: "stack-large" }, greeting(ctx), summaryCard(summary));
}
