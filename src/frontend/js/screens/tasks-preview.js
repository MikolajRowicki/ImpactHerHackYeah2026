import { h } from "../dom.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { emptyState } from "../ui/feedback.js";
import { section } from "../ui/layout.js";

const SHOWN = 3;

// A few open tasks on a start screen, with a link to the whole list.
export function tasksPreview(items, { title, empty }) {
  const open = items.filter((task) => task.status === "open");
  return section(
    {
      title,
      id: "tasks-preview-title",
      action: h("a", { class: "section__link", href: "#/tasks" }, t.wellbeing.allTasks),
    },
    open.length === 0
      ? emptyState({ iconName: "tasks", text: empty })
      : h(
          "ul",
          { class: "card-list tasks-preview" },
          ...open.slice(0, SHOWN).map((task) =>
            h(
              "li",
              { class: "card tasks-preview__item" },
              h("span", { class: "icon-badge" }, icon("tasks", 20)),
              h(
                "div",
                {},
                h("p", { class: "task-row__title" }, task.title),
                task.details && h("p", { class: "task-row__meta" }, task.details),
              ),
            ),
          ),
        ),
  );
}
