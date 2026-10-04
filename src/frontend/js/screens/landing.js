import { h } from "../dom.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { linkButton } from "../ui/layout.js";

const SVG = "http://www.w3.org/2000/svg";

function svg(tag, attrs = {}, ...children) {
  const node = document.createElementNS(SVG, tag);
  for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, value);
  node.append(...children);
  return node;
}

// A four-pointed star, the one accent that repeats through the page.
function sparkle(className) {
  return svg(
    "svg",
    { class: `sparkle ${className}`, viewBox: "0 0 24 24", "aria-hidden": "true", focusable: "false" },
    svg("path", { d: "M12 0c1 7 5 11 12 12-7 1-11 5-12 12-1-7-5-11-12-12 7-1 11-5 12-12Z" }),
  );
}

function dots(className) {
  const pattern = svg(
    "pattern",
    { id: `dots-${className}`, width: "14", height: "14", patternUnits: "userSpaceOnUse" },
    svg("circle", { cx: "3", cy: "3", r: "2" }),
  );
  return svg(
    "svg",
    { class: `dots ${className}`, viewBox: "0 0 112 112", "aria-hidden": "true", focusable: "false" },
    svg("defs", {}, pattern),
    svg("rect", { width: "112", height: "112", fill: `url(#dots-${className})` }),
  );
}

function wave() {
  return svg(
    "svg",
    { class: "wave", viewBox: "0 0 120 10", "aria-hidden": "true", focusable: "false" },
    svg("path", {
      d: "M2 5c8-6 14-6 20 0s12 6 20 0 14-6 20 0 12 6 20 0 14-6 20 0",
      fill: "none",
      "stroke-width": "3",
      "stroke-linecap": "round",
    }),
  );
}

// A small copy of the app's start, drawn in markup. It is decoration, so it is hidden from
// assistive technology.
function phone() {
  const p = t.landing.phone;
  return h(
    "div",
    { class: "phone", "aria-hidden": "true" },
    h("div", { class: "phone__bar" }, h("span", {}, "9:41"), h("span", { class: "phone__notch" })),
    h("div", { class: "phone__brand" }, icon("leaf", 14), t.landing.brand),
    h("p", { class: "phone__greeting" }, p.greeting),
    h(
      "div",
      { class: "phone__card" },
      h("strong", {}, p.cardTitle),
      h("span", {}, p.cardText),
    ),
    h(
      "div",
      { class: "phone__summary" },
      h("strong", {}, p.summary),
      h("span", {}, p.summaryText),
    ),
  );
}

function hero() {
  const [first, second] = t.landing.heroTitleLines;
  return h(
    "header",
    { class: "landing__hero" },
    h(
      "div",
      { class: "landing__hero-text" },
      h("p", { class: "landing__brand" }, t.landing.brand),
      h(
        "h1",
        {},
        h("span", { class: "landing__line landing__line--green" }, first),
        " ",
        h("span", { class: "landing__line landing__line--coral" }, second),
      ),
      h("p", { class: "script landing__script" }, t.landing.heroScript),
      wave(),
      h("p", { class: "landing__lead" }, t.landing.heroLead),
      h(
        "div",
        { class: "actions" },
        linkButton("#/register", t.landing.signUp, { variant: "accent", iconName: "heart" }),
        linkButton("#/login", t.landing.signIn, { variant: "ghost" }),
      ),
    ),
    h(
      "div",
      { class: "landing__stage", "aria-hidden": "true" },
      dots("dots--stage"),
      h("div", { class: "landing__arch" }, h("div", { class: "landing__sun" })),
      phone(),
      sparkle("sparkle--one"),
      sparkle("sparkle--two"),
    ),
  );
}

function voices() {
  return h(
    "section",
    { class: "landing__band landing__band--peach", "aria-labelledby": "landing-voices" },
    h(
      "div",
      { class: "landing__voices" },
      h(
        "div",
        { class: "landing__notes" },
        h("h2", { id: "landing-voices", class: "script" }, t.landing.voicesTitle),
        h(
          "ul",
          { class: "notes" },
          ...t.landing.voices.map((text, i) => h("li", { class: `note note--${i + 1}` }, text)),
        ),
      ),
      h(
        "div",
        { class: "landing__signals" },
        h("h2", { class: "script script--coral" }, t.landing.signalsTitle),
        h(
          "ul",
          { class: "signals" },
          ...t.landing.signals.map((text) =>
            h("li", {}, h("span", { class: "signals__mark" }, icon("check", 18)), text),
          ),
        ),
      ),
    ),
    h("p", { class: "landing__voices-note" }, sparkle("sparkle--inline"), t.landing.voicesNote),
  );
}

const ROLE_TONE = { woman: "coral", partner: "green", supporter: "mustard" };

function roles() {
  return h(
    "section",
    { class: "landing__section", "aria-labelledby": "landing-roles" },
    h("h2", { id: "landing-roles" }, t.landing.rolesTitle),
    h(
      "div",
      { class: "landing__roles" },
      ...t.landing.roles.map((role) =>
        h(
          "article",
          { class: "landing__role" },
          h("span", { class: `badge badge--${ROLE_TONE[role.key]}` }, icon(role.icon, 26)),
          h("h3", {}, role.title),
          h("p", {}, role.text),
        ),
      ),
    ),
  );
}

const STEP_TONES = ["coral", "green", "mustard"];

function steps() {
  return h(
    "section",
    { class: "landing__section", "aria-labelledby": "landing-steps" },
    h("h2", { id: "landing-steps" }, t.landing.stepsTitle),
    h(
      "ol",
      { class: "landing__steps" },
      ...t.landing.steps.map((step, i) =>
        h(
          "li",
          { class: `step step--${STEP_TONES[i]}` },
          h("div", {}, h("h3", {}, step.title), h("p", {}, step.text)),
        ),
      ),
    ),
  );
}

function privacy() {
  const mark = (sees) =>
    h(
      "td",
      {},
      h(
        "span",
        { class: `see see--${sees ? "yes" : "no"}` },
        icon(sees ? "check" : "close", 18),
        h("span", { class: "visually-hidden" }, sees ? t.landing.yes : t.landing.no),
      ),
    );
  return h(
    "section",
    { class: "landing__section landing__privacy", "aria-labelledby": "landing-privacy" },
    h("h2", { id: "landing-privacy" }, t.landing.privacyTitle),
    h("p", { class: "script landing__script" }, t.landing.privacyScript),
    h("p", { class: "landing__privacy-lead" }, t.landing.privacyLead),
    h(
      "table",
      { class: "see-table" },
      h(
        "thead",
        {},
        h(
          "tr",
          {},
          h("td", {}),
          ...t.landing.privacyColumns.map((name, i) =>
            h("th", { scope: "col", class: `see-table__col see-table__col--${STEP_TONES[i]}` }, name),
          ),
        ),
      ),
      h(
        "tbody",
        {},
        ...t.landing.privacyRows.map((row) =>
          h("tr", {}, h("th", { scope: "row" }, row.label), ...row.sees.map(mark)),
        ),
      ),
    ),
  );
}

function safety() {
  return h(
    "section",
    { class: "landing__band landing__band--green", "aria-labelledby": "landing-safety" },
    h(
      "div",
      { class: "landing__safety" },
      h(
        "div",
        {},
        h("h2", { id: "landing-safety" }, t.landing.safetyTitle),
        h(
          "ul",
          { class: "safety-list" },
          ...t.landing.safetyItems.map((text) => h("li", {}, sparkle("sparkle--inline"), text)),
        ),
        h("a", { class: "landing__help-link", href: "#/help" }, t.landing.helpLink),
      ),
      h(
        "div",
        { class: "landing__lines" },
        h("p", { class: "script script--mustard" }, t.landing.safetyScript),
        h(
          "ul",
          { class: "lines" },
          ...t.landing.safetyLines.map((line) =>
            h("li", {}, h("strong", {}, line.number), h("span", {}, line.note)),
          ),
        ),
      ),
    ),
  );
}

function final() {
  return h(
    "section",
    { class: "landing__final", "aria-labelledby": "landing-final" },
    h("h2", { id: "landing-final" }, t.landing.finalTitle),
    h("p", {}, t.landing.finalText),
    h(
      "div",
      { class: "actions" },
      linkButton("#/register", t.landing.signUp, { variant: "accent" }),
      linkButton("#/login", t.landing.signIn, { variant: "ghost" }),
    ),
  );
}

// One calm motion: the phone and the stars settle in when the page opens. It is added by the
// script, only when the person has not asked for less, and nothing needs it to be read.
function settle(root) {
  const calm = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  if (calm) return;
  root.classList.add("landing--motion");
}

// `#/` for a signed-out visitor.
export function landing() {
  const root = h(
    "div",
    { class: "landing" },
    hero(),
    voices(),
    roles(),
    steps(),
    privacy(),
    safety(),
    final(),
  );
  settle(root);
  root.dataset.wide = "true";
  return root;
}
