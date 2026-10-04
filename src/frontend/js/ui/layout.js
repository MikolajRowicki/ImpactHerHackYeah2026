import { h } from "../dom.js";
import { icon } from "../icons.js";

// The one h1 of a screen, with an optional line above and a lead below.
export function pageHead({ title, eyebrow, eyebrowIcon, lead }) {
  return h(
    "header",
    { class: "page-head" },
    eyebrow &&
      h("p", { class: "page-head__eyebrow" }, eyebrowIcon && icon(eyebrowIcon, 18), eyebrow),
    h("h1", {}, title),
    lead && h("p", { class: "page-head__lead" }, lead),
  );
}

export function screen(...children) {
  return h("div", { class: "stack-large" }, ...children);
}

export function card({ tone, className, label } = {}, ...children) {
  const classes = ["card", tone && `card--${tone}`, className].filter(Boolean).join(" ");
  return h("div", { class: classes, "aria-label": label }, ...children);
}

// A titled part of a screen: an h2 and its content, with an optional link or button on the right.
export function section({ title, action, id, className } = {}, ...children) {
  const headingId = id || `section-${title.replace(/\W+/g, "-").toLowerCase()}`;
  return h(
    "section",
    { class: ["section", className].filter(Boolean).join(" "), "aria-labelledby": headingId },
    h("div", { class: "section__head" }, h("h2", { id: headingId }, title), action),
    ...children,
  );
}

// A whole-screen message: not found, not allowed, closed group, failure.
export function stateScreen({ iconName = "leaf", title, text, actions = [] }) {
  return h(
    "div",
    { class: "state-screen" },
    h("span", { class: "icon-badge" }, icon(iconName, 30)),
    h("h1", {}, title),
    ...[].concat(text || []).map((line) => h("p", { class: "muted" }, line)),
    actions.length ? h("div", { class: "actions" }, ...actions) : null,
  );
}

export function linkButton(href, label, { variant, iconName, small } = {}) {
  const classes = ["button", variant && `button--${variant}`, small && "button--small"];
  return h(
    "a",
    { class: classes.filter(Boolean).join(" "), href },
    iconName && icon(iconName, 20),
    label,
  );
}

export function button(label, { variant, iconName, small, onclick, type = "button" } = {}) {
  const classes = ["button", variant && `button--${variant}`, small && "button--small"];
  return h(
    "button",
    { class: classes.filter(Boolean).join(" "), type, onclick },
    iconName && icon(iconName, 20),
    label,
  );
}

// A large link card, used for the main next step of a start screen. A quiet one is for a tool
// that waits next to the main step.
export function ctaCard(href, iconName, title, lead, { quiet = false } = {}) {
  return h(
    "a",
    { class: quiet ? "cta-card cta-card--quiet" : "cta-card", href },
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
