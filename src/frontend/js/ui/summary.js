import { h } from "../dom.js";
import { dateTime } from "../format.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { crisisLines } from "./crisis-lines.js";

// One calm icon per trend. No colour carries meaning on its own, and none of them is red.
const TREND_ICONS = { stable: "leaf", uncertain: "cloud", needs_attention: "heart" };

export function summaryCard(summary) {
  const reader = summary.audience === "woman" ? "woman" : "loved";
  const trend = t.summary.trend[summary.trend] || t.summary.trend.uncertain;
  const headingId = "summary-title";

  return h(
    "section",
    { class: "summary", "aria-labelledby": headingId },
    h("div", { class: "summary__head" }, h("h2", { id: headingId }, t.summary.title)),
    h(
      "div",
      { class: `summary__trend summary__trend--${summary.trend}` },
      h("span", { class: "icon-badge" }, icon(TREND_ICONS[summary.trend] || "cloud")),
      h(
        "div",
        {},
        h("p", { class: "summary__trend-text" }, trend[reader]),
        summary.trend === "needs_attention" &&
          h(
            "a",
            { class: "summary__help", href: "#/help" },
            t.summary.helpLink,
            icon("arrow", 18),
          ),
      ),
    ),
    summary.statements.length > 0 &&
      h(
        "ul",
        { class: "summary__statements" },
        ...summary.statements.map((line) => h("li", {}, line)),
      ),
    summary.reasons?.length > 0 &&
      h(
        "div",
        { class: "summary__reasons" },
        h("h3", {}, t.summary.reasonsTitle),
        h("ul", {}, ...summary.reasons.map((line) => h("li", {}, line))),
      ),
    summary.help &&
      h(
        "section",
        { class: "summary__crisis", "aria-label": t.summary.crisisTitle },
        h("h3", {}, t.summary.crisisTitle),
        crisisLines(summary.help.crisis_lines),
      ),
    summary.care_reminder &&
      h(
        "aside",
        { class: "summary__reminder", "aria-label": t.summary.reminderTitle },
        h("span", { class: "icon-badge icon-badge--accent" }, icon("hand")),
        h(
          "div",
          {},
          h("h3", {}, t.summary.reminderTitle),
          h("p", { class: "summary__reminder-text" }, summary.care_reminder),
        ),
      ),
    // A mock narrative is placeholder text; people never see it.
    summary.narrative &&
      summary.narrative.source !== "mock" &&
      h("figure", { class: "summary__narrative" }, h("p", {}, summary.narrative.text)),
    h(
      "p",
      { class: "summary__time" },
      h("time", { datetime: summary.generated_at }, t.summary.generated(dateTime(summary.generated_at))),
    ),
  );
}
