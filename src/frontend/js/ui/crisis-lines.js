import { h } from "../dom.js";
import { icon } from "../icons.js";

// "116 123" dials as "tel:116123"; a plus sign for a country code is kept.
export function telHref(number) {
  return `tel:${number.replace(/[^\d+]/g, "")}`;
}

// The crisis lines as a list: name, a number that dials, hours and a short description.
export function crisisLines(lines) {
  return h(
    "ul",
    { class: "crisis-lines" },
    ...lines.map((line) =>
      h(
        "li",
        { class: "card crisis-line" },
        h("span", { class: "icon-badge icon-badge--accent" }, icon("phone")),
        h(
          "div",
          { class: "crisis-line__text" },
          h("h3", { class: "crisis-line__name" }, line.name),
          h(
            "p",
            { class: "crisis-line__number" },
            h("a", { href: telHref(line.number) }, line.number),
            h("span", { class: "crisis-line__hours" }, line.hours),
          ),
          h("p", { class: "crisis-line__description" }, line.description),
        ),
      ),
    ),
  );
}
