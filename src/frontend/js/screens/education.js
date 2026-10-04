import { h } from "../dom.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { notice } from "../ui/feedback.js";
import { linkButton, pageHead } from "../ui/layout.js";

function educationSection(item) {
  const headingId = `education-${item.id}`;
  return h(
    "section",
    { class: "card education__section", "aria-labelledby": headingId },
    h("h2", { id: headingId, class: "card__title" }, icon(item.icon, 22), item.title),
    ...(item.paragraphs || []).map((text) => h("p", {}, text)),
    item.items && h("ul", { class: "education__list" }, ...item.items.map((text) => h("li", {}, text))),
  );
}

// General knowledge for everyone, whatever role and whether or not there is a group.
export async function education() {
  return h(
    "div",
    { class: "education stack-large" },
    pageHead({ title: t.education.title, eyebrowIcon: "book", lead: t.education.lead }),
    notice({ tone: "accent", iconName: "info" }, t.education.note),
    ...t.education.sections.map(educationSection),
    h(
      "div",
      { class: "actions" },
      linkButton("#/help", t.education.helpLink, { variant: "accent", iconName: "lifebuoy" }),
    ),
  );
}
