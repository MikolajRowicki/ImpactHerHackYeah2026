import { ApiError } from "../api.js";
import { h } from "../dom.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { button, stateScreen } from "./layout.js";

// The Polish message from an error body, or a general one when there is no body.
export function messageOf(error, fallback = t.common.actionFailed) {
  if (error instanceof ApiError && error.code !== "unknown") return error.message;
  return fallback;
}

export function loading() {
  return h(
    "p",
    { class: "loading", role: "status" },
    h("span", { class: "loading__dot", "aria-hidden": "true" }),
    t.common.loading,
  );
}

export function errorState(error, onRetry) {
  return stateScreen({
    iconName: "cloud",
    title: t.common.failedTitle,
    text: messageOf(error, t.common.failed),
    actions: [button(t.common.retry, { iconName: "arrow", onclick: onRetry })],
  });
}

export function emptyState({ iconName = "leaf", text, action }) {
  return h("div", { class: "empty" }, icon(iconName, 32), h("p", {}, text), action);
}

// A message box. `tone` is error, success, accent or nothing.
export function notice({ tone, iconName = "info", role } = {}, ...lines) {
  return h(
    "div",
    { class: ["notice", tone && `notice--${tone}`].filter(Boolean).join(" "), role },
    icon(iconName, 20),
    h("div", {}, ...lines.map((line) => (typeof line === "string" ? h("p", {}, line) : line))),
  );
}

// A place for the result of an action, announced to screen readers when it changes.
export function messageSlot() {
  const node = h("div", { class: "message-slot", "aria-live": "polite" });
  return {
    node,
    error(text) {
      node.replaceChildren(notice({ tone: "error", iconName: "info", role: "alert" }, text));
    },
    success(text) {
      node.replaceChildren(notice({ tone: "success", iconName: "check" }, text));
    },
    clear() {
      node.replaceChildren();
    },
  };
}
