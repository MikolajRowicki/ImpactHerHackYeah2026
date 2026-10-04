import { h } from "../dom.js";
import { icon } from "../icons.js";

let counter = 0;
const uid = (name) => `f-${name}-${++counter}`;

function errorLine(id) {
  return h("p", { class: "field__error", id });
}

function showError(line, text) {
  line.replaceChildren(...(text ? [icon("info", 16), text] : []));
}

// A labelled input. The error line and hint are tied to it with aria-describedby.
export function field({
  label,
  name,
  type = "text",
  value = "",
  hint,
  autocomplete,
  maxlength,
  multiline = false,
  required = false,
}) {
  const id = uid(name);
  const hintId = hint ? `${id}-hint` : null;
  const errorId = `${id}-error`;
  const attrs = {
    id,
    name,
    class: "field__input",
    autocomplete,
    maxlength,
    required,
    "aria-describedby": [hintId, errorId].filter(Boolean).join(" "),
  };
  const input = multiline
    ? h("textarea", { ...attrs, rows: 3 })
    : h("input", { ...attrs, type });
  input.value = value;
  const error = errorLine(errorId);
  const node = h(
    "div",
    { class: "field" },
    h("label", { class: "field__label", for: id }, label),
    hint && h("p", { class: "field__hint", id: hintId }, hint),
    input,
    error,
  );
  return {
    node,
    input,
    get value() {
      return input.value;
    },
    setError(text) {
      showError(error, text);
      if (text) input.setAttribute("aria-invalid", "true");
      else input.removeAttribute("aria-invalid");
    },
  };
}

// Radio buttons shown as cards, inside a fieldset whose legend names the group.
export function choiceGroup({ legend, name, options, value = null, hint }) {
  const id = uid(name);
  const errorId = `${id}-error`;
  const hintId = hint ? `${id}-hint` : null;
  const inputs = options.map((option) =>
    h("input", {
      type: "radio",
      name: id,
      value: option.value,
      checked: option.value === value,
      "aria-describedby": [hintId, errorId].filter(Boolean).join(" "),
    }),
  );
  const error = errorLine(errorId);
  const node = h(
    "fieldset",
    { class: "choice-group" },
    h("legend", {}, legend),
    hint && h("p", { class: "field__hint", id: hintId }, hint),
    h(
      "div",
      { class: "choice-group__options" },
      ...options.map((option, i) =>
        h(
          "label",
          { class: "choice" },
          inputs[i],
          h("span", { class: "choice__mark", "aria-hidden": "true" }),
          h("span", { class: "choice__label" }, option.label),
        ),
      ),
    ),
    error,
  );
  for (const input of inputs) input.addEventListener("change", () => setError(""));
  function setError(text) {
    showError(error, text);
    if (text) node.setAttribute("aria-invalid", "true");
    else node.removeAttribute("aria-invalid");
  }
  return {
    node,
    get value() {
      const checked = inputs.find((input) => input.checked);
      return checked ? checked.value : null;
    },
    setError,
    focus() {
      inputs[0]?.focus();
    },
  };
}

export function submitButton(label, { variant, iconName } = {}) {
  const classes = ["button", variant && `button--${variant}`].filter(Boolean).join(" ");
  return h("button", { class: classes, type: "submit" }, iconName && icon(iconName, 20), label);
}

// Runs `work` with the button marked busy, so a second press does not send twice.
// With `label`, the button says it while it waits (for example "Przygotowuję…").
export async function whileBusy(button, work, { label } = {}) {
  if (button.getAttribute("aria-busy") === "true") return undefined;
  button.setAttribute("aria-busy", "true");
  button.disabled = true;
  const content = label ? [...button.childNodes] : null;
  if (label) button.replaceChildren(label);
  try {
    return await work();
  } finally {
    button.removeAttribute("aria-busy");
    button.disabled = false;
    if (content) button.replaceChildren(...content);
  }
}

// Puts the messages from a 422 answer next to their fields. Returns true if any matched.
export function showFieldErrors(error, fields) {
  let shown = false;
  for (const [name, message] of Object.entries(error.fields || {})) {
    if (fields[name]) {
      fields[name].setError(message);
      shown = true;
    }
  }
  return shown;
}
