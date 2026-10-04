import { h } from "../dom.js";
import { t } from "../strings.pl.js";
import { button } from "./layout.js";

// A native modal dialog. Resolves true when confirmed and false on cancel or Escape.
export function confirmDialog({ title, text, confirmLabel, danger = false }) {
  return new Promise((resolve) => {
    let confirmed = false;
    const headingId = `dialog-${Date.now()}`;
    const dialog = h("dialog", { class: "dialog", "aria-labelledby": headingId });
    const cancel = button(t.common.cancel, { variant: "quiet", onclick: () => dialog.close() });
    const confirm = button(confirmLabel, {
      variant: danger ? "danger" : undefined,
      onclick: () => {
        confirmed = true;
        dialog.close();
      },
    });
    dialog.append(
      h(
        "div",
        { class: "dialog__body" },
        h("h2", { id: headingId }, title),
        ...[].concat(text).map((line) => h("p", {}, line)),
        h("div", { class: "actions" }, cancel, confirm),
      ),
    );
    dialog.addEventListener("close", () => {
      dialog.remove();
      resolve(confirmed);
    });
    document.body.append(dialog);
    dialog.showModal();
    cancel.focus();
  });
}

// A native modal dialog around any content. `content` receives `close` so it can end itself.
export function openDialog({ title, content }) {
  const headingId = `dialog-${Date.now()}`;
  const dialog = h("dialog", { class: "dialog dialog--wide", "aria-labelledby": headingId });
  const close = () => dialog.close();
  const closeButton = button(t.group.closeDialog, { variant: "quiet", onclick: close });
  dialog.append(
    h(
      "div",
      { class: "dialog__body" },
      h("h2", { id: headingId }, title),
      content(close),
      h("div", { class: "actions" }, closeButton),
    ),
  );
  dialog.addEventListener("close", () => dialog.remove());
  document.body.append(dialog);
  dialog.showModal();
  return close;
}
