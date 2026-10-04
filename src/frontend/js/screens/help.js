import { ApiError } from "../api.js";
import { h } from "../dom.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { crisisLines } from "../ui/crisis-lines.js";
import { messageOf, notice } from "../ui/feedback.js";
import { button, linkButton, pageHead, section } from "../ui/layout.js";

function notADoctor() {
  const block = (iconName, title, text) =>
    h(
      "div",
      { class: "card help-card" },
      h("span", { class: "icon-badge" }, icon(iconName)),
      h("div", {}, h("h2", {}, title), h("p", {}, text)),
    );
  return h(
    "div",
    { class: "help__list" },
    block("info", t.help.notADoctorTitle, t.help.notADoctor),
    block("heart", t.help.talkTitle, t.help.talk),
  );
}

function head() {
  return pageHead({ title: t.help.title, eyebrowIcon: "lifebuoy", lead: t.help.lead });
}

// The one number that is always known, also when nothing else could be read.
const emergency = () => crisisLines([t.help.emergency]);

function path(steps) {
  return section(
    { title: t.help.pathTitle, id: "help-path-title" },
    h(
      "ol",
      { class: "help-path" },
      ...[...steps]
        .sort((a, b) => a.order - b.order)
        .map((step) =>
          h(
            "li",
            { class: "card help-path__step" },
            h("h3", {}, step.title),
            h("p", {}, step.description),
          ),
        ),
    ),
  );
}

function regional(contact) {
  return section(
    { title: t.help.regionalTitle, id: "help-regional-title" },
    h(
      "div",
      { class: "card" },
      h("h3", {}, contact.name),
      h("p", {}, contact.description),
      linkButton(contact.url, t.help.regionalLink, { variant: "ghost", iconName: "link" }),
    ),
  );
}

// `#/help`: crisis lines and a care path for a signed-in person, only 112 for anyone else.
export async function help(ctx) {
  if (!ctx.session.me) return signedOut();
  let answer;
  try {
    answer = await ctx.api.call("get_help");
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return signedOut();
    return failed(ctx, error);
  }
  return h(
    "div",
    { class: "help stack-large" },
    head(),
    section({ title: t.help.linesTitle, id: "help-lines-title" }, crisisLines(answer.crisis_lines)),
    path(answer.path),
    answer.regional_contact && regional(answer.regional_contact),
    notADoctor(),
  );
}

function signedOut() {
  return h(
    "div",
    { class: "help stack-large" },
    head(),
    section({ title: t.help.signedOutTitle, id: "help-lines-title" }, emergency()),
    notice({ iconName: "info" }, t.help.signedOutText),
    h("div", { class: "actions" }, linkButton("#/login", t.help.signedOutLink, { variant: "accent" })),
    notADoctor(),
  );
}

function failed(ctx, error) {
  return h(
    "div",
    { class: "help stack-large" },
    head(),
    section({ title: t.help.failedTitle, id: "help-lines-title" }, emergency()),
    notice({ tone: "error", iconName: "info", role: "alert" }, messageOf(error, t.help.failedText)),
    h(
      "div",
      { class: "actions" },
      button(t.common.retry, { iconName: "arrow", onclick: () => ctx.refresh() }),
    ),
    notADoctor(),
  );
}
