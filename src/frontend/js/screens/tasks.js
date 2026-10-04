import { ApiError } from "../api.js";
import { h } from "../dom.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { emptyState, messageOf, messageSlot, notice } from "../ui/feedback.js";
import { field, showFieldErrors, submitButton, whileBusy } from "../ui/forms.js";
import { button, pageHead, section } from "../ui/layout.js";

const TITLE_MAX = 120;
const DETAILS_MAX = 500;
const STATES = ["open", "claimed", "done"];

// Who added and who took a task. No counts per person and no ranking, on purpose.
function meta(task, me) {
  const name = (person) => (person.id === me.id ? t.tasks.you : person.display_name);
  const lines = [t.tasks.addedBy(name(task.created_by))];
  if (task.status === "claimed") lines.push(t.tasks.takenBy(name(task.claimed_by)));
  if (task.status === "done") lines.push(t.tasks.doneBy(name(task.claimed_by)));
  return lines.join(" · ");
}

function addForm(ctx, onAdded) {
  const message = messageSlot();
  const title = field({
    label: t.tasks.taskTitle,
    name: "title",
    hint: t.tasks.taskTitleHint,
    maxlength: TITLE_MAX,
    autocomplete: "off",
  });
  const details = field({
    label: t.tasks.details,
    name: "details",
    hint: t.tasks.detailsHint,
    maxlength: DETAILS_MAX,
    multiline: true,
  });
  const submit = submitButton(t.tasks.add, { variant: "accent", iconName: "plus" });
  const form = h(
    "form",
    { class: "form task-form", novalidate: true },
    title.node,
    details.node,
    message.node,
    submit,
  );

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.clear();
    const titleText = title.value.trim();
    const detailsText = details.value.trim();
    title.setError(
      !titleText ? t.tasks.titleMissing : titleText.length > TITLE_MAX ? t.tasks.titleLong : "",
    );
    details.setError(detailsText.length > DETAILS_MAX ? t.tasks.detailsLong : "");
    if (!titleText || titleText.length > TITLE_MAX) {
      title.input.focus();
      return;
    }
    if (detailsText.length > DETAILS_MAX) return;
    const body = { title: titleText };
    if (detailsText) body.details = detailsText;
    await whileBusy(submit, async () => {
      try {
        await ctx.api.call("create_task", { body });
      } catch (error) {
        if (error instanceof ApiError && error.status === 422) {
          showFieldErrors(error, { title, details });
        }
        message.error(messageOf(error));
        return;
      }
      title.input.value = "";
      details.input.value = "";
      message.success(t.tasks.added);
      await onAdded();
    });
  });
  return form;
}

// Ready-made ideas for an active group. Each one becomes a task with its own title and details.
function ideasCard(ctx, items, { onAdded, message }) {
  async function add(item, control) {
    message.clear();
    await whileBusy(control, async () => {
      try {
        await ctx.api.call("create_task", {
          body: { title: item.title, ...(item.details ? { details: item.details } : {}) },
        });
      } catch (error) {
        message.error(messageOf(error));
        return;
      }
      message.success(t.tasks.ideaAdded(item.title));
      await onAdded();
    });
  }

  return h(
    "section",
    { class: "card task-ideas", "aria-labelledby": "task-ideas-title" },
    h("h2", { id: "task-ideas-title", class: "card__title" }, icon("sparkle"), t.tasks.ideasTitle),
    h("p", { class: "muted" }, t.tasks.ideasLead),
    h(
      "ul",
      { class: "task-ideas__list" },
      ...items.map((item) => {
        const control = button(t.tasks.ideaAdd, { small: true, iconName: "plus" });
        control.setAttribute("aria-label", t.tasks.ideaAddLabel(item.title));
        control.addEventListener("click", () => add(item, control));
        return h(
          "li",
          { class: "task-idea" },
          h(
            "div",
            { class: "task-idea__text" },
            h("h3", { class: "task-idea__title" }, item.title),
            item.details && h("p", { class: "task__details" }, item.details),
          ),
          control,
        );
      }),
    ),
  );
}

export async function tasks(ctx) {
  const me = ctx.session.me;
  const closed = ctx.session.groupStatus === "closed";
  const message = messageSlot();
  const listBox = h("div", { class: "task-lists" });

  async function act(operation, task, control) {
    message.clear();
    await whileBusy(control, async () => {
      try {
        await ctx.api.call(operation, { params: { task_id: task.id } });
      } catch (error) {
        message.error(messageOf(error));
      }
      // Reload either way: after a conflict the list shows who took the task first.
      await reload();
      // The pressed button is gone; keep keyboard focus on the task where it now stands.
      listBox.querySelector(`[data-task-id="${task.id}"]`)?.focus();
    });
  }

  function taskItem(task) {
    let control = null;
    if (!closed && task.status === "open") {
      control = button(t.tasks.take, { small: true, iconName: "hand" });
      control.addEventListener("click", () => act("claim_task", task, control));
    } else if (!closed && task.status === "claimed" && task.claimed_by?.id === me.id) {
      const finish = button(t.tasks.finish, { small: true, variant: "ghost", iconName: "check" });
      finish.addEventListener("click", () => act("complete_task", task, finish));
      const release = button(t.tasks.release, { small: true, variant: "quiet", iconName: "back" });
      release.addEventListener("click", () => act("release_task", task, release));
      control = h("div", { class: "task__actions" }, finish, release);
    }
    return h(
      "li",
      { class: `card task task--${task.status}`, "data-task-id": task.id, tabindex: "-1" },
      h(
        "div",
        { class: "task-row" },
        h(
          "div",
          { class: "task-row__text" },
          h("h3", { class: "task-row__title" }, task.title),
          task.details && h("p", { class: "task__details" }, task.details),
          h("p", { class: "task-row__meta" }, meta(task, me)),
        ),
        control,
      ),
    );
  }

  function render(items) {
    if (items.length === 0) {
      listBox.replaceChildren(emptyState({ iconName: "tasks", text: t.tasks.empty }));
      return;
    }
    listBox.replaceChildren(
      ...STATES.map((state) => {
        const inState = items.filter((task) => task.status === state);
        return section(
          { title: t.tasks[state], id: `tasks-${state}` },
          inState.length
            ? h("ul", { class: "card-list" }, ...inState.map(taskItem))
            : h("p", { class: "muted" }, t.tasks.noneHere),
        );
      }),
    );
  }

  async function reload() {
    try {
      const { items } = await ctx.api.call("list_tasks");
      render(items);
    } catch (error) {
      message.error(messageOf(error));
    }
  }

  render((await ctx.api.call("list_tasks")).items);

  // The ideas are a help, not the screen's job: when they cannot be read the list still works.
  let ideas = null;
  if (ctx.session.groupStatus === "active") {
    try {
      const { items } = await ctx.api.call("list_task_suggestions");
      if (items.length) ideas = ideasCard(ctx, items, { onAdded: reload, message });
    } catch {
      ideas = null;
    }
  }

  const node = h(
    "div",
    { class: "tasks" },
    pageHead({ title: t.tasks.title, eyebrowIcon: "tasks", lead: t.tasks.lead }),
    h(
      "div",
      { class: "start-grid" },
      h("div", { class: "start-grid__main" }, message.node, listBox),
      h(
        "div",
        { class: "start-grid__side" },
        closed
          ? notice({ tone: "accent", iconName: "lock" }, t.tasks.closed)
          : h(
              "section",
              { class: "card task-add", "aria-labelledby": "task-add-title" },
              h("h2", { id: "task-add-title", class: "card__title" }, icon("plus"), t.tasks.addTitle),
              addForm(ctx, reload),
            ),
        ideas,
      ),
    ),
  );
  node.dataset.wide = "true";
  return node;
}
