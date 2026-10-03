import { h } from "../dom.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { pageHead } from "../ui/layout.js";

// A calm placeholder for the help path. It shows no phone numbers until the contract has them.
export function help() {
  const block = (iconName, title, text) =>
    h(
      "div",
      { class: "card help-card" },
      h("span", { class: "icon-badge" }, icon(iconName)),
      h("div", {}, h("h2", {}, title), h("p", {}, text)),
    );
  return h(
    "div",
    { class: "help" },
    pageHead({ title: t.help.title, eyebrowIcon: "lifebuoy", lead: t.help.lead }),
    h(
      "div",
      { class: "help__list" },
      block("clock", t.help.comingTitle, t.help.coming),
      block("heart", t.help.talkTitle, t.help.talk),
      block("info", t.help.notADoctorTitle, t.help.notADoctor),
    ),
  );
}
