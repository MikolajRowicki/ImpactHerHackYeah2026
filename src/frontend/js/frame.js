import { h } from "./dom.js";
import { icon } from "./icons.js";
import { PERSPECTIVES } from "./mock-store.js";
import { t } from "./strings.pl.js";
import { isDark, onSystemChange, setTheme } from "./theme.js";

// Navigation items in order. `show` decides from the signed-in person who sees the item.
const isActiveOrClosed = (m) => m && m.group_status !== "pending";
const NAV = [
  { path: "/login", label: () => t.nav.login, iconName: "login", show: (me) => !me },
  { path: "/", label: () => t.nav.start, iconName: "home", show: (me) => Boolean(me) },
  {
    path: "/check-in",
    label: () => t.nav.checkIn,
    iconName: "leaf",
    show: (me) => isActiveOrClosed(me?.membership) && me.membership.role === "woman",
  },
  {
    path: "/questions",
    label: () => t.nav.questions,
    iconName: "chat",
    show: (me) => me?.membership?.group_status === "active" && me.membership.role !== "woman",
  },
  {
    path: "/tasks",
    label: () => t.nav.tasks,
    iconName: "tasks",
    show: (me) => isActiveOrClosed(me?.membership),
  },
  { path: "/group", label: () => t.nav.group, iconName: "people", show: (me) => Boolean(me?.membership) },
  { path: "/help", label: () => t.nav.help, iconName: "lifebuoy", show: () => true },
];

export function navItems(me) {
  return NAV.filter((item) => item.show(me));
}

function themeButton() {
  const button = h(
    "button",
    { class: "icon-button theme-switch", type: "button", "aria-label": t.theme.dark, title: t.theme.dark },
  );
  const sync = () => {
    const dark = isDark();
    button.setAttribute("aria-pressed", String(dark));
    button.replaceChildren(icon(dark ? "sun" : "moon"));
  };
  button.addEventListener("click", () => {
    setTheme(isDark() ? "light" : "dark");
    sync();
  });
  onSystemChange(sync);
  sync();
  return button;
}

export function createFrame({ onSignOut }) {
  const inner = document.getElementById("header-inner");
  const brand = h(
    "a",
    { class: "brand", href: "#/" },
    h("span", { class: "brand__mark" }, icon("leaf", 20)),
    t.common.appName,
  );
  const nav = h("nav", { class: "site-nav", "aria-label": t.nav.label });
  const signOut = h(
    "button",
    { class: "text-button sign-out", type: "button", onclick: onSignOut },
    icon("logout", 20),
    h("span", { class: "sign-out__label" }, t.nav.signOut),
  );
  const actions = h("div", { class: "header-actions" }, themeButton(), signOut);
  inner.replaceChildren(brand, nav, actions);

  return {
    update(me, path) {
      const items = navItems(me);
      nav.replaceChildren(
        h(
          "ul",
          {},
          ...items.map((item) =>
            h(
              "li",
              {},
              h(
                "a",
                { href: `#${item.path}`, "aria-current": item.path === path ? "page" : null },
                h("span", { class: "nav-icon" }, icon(item.iconName)),
                h("span", { class: "nav-label" }, item.label()),
              ),
            ),
          ),
        ),
      );
      document.body.classList.toggle("has-nav", items.length > 0);
      signOut.hidden = !me;
    },
  };
}

// The demo notice: says the data is a sample, switches the perspective and resets the demo.
export function mockNotice({ current, onPerspective, onReset }) {
  const select = h(
    "select",
    { name: "perspective" },
    current === "" && h("option", { value: "", selected: true, disabled: true }, t.mock.signedOut),
    current === "other" && h("option", { value: "other", selected: true, disabled: true }, t.mock.other),
    ...PERSPECTIVES.map((key) =>
      h("option", { value: key, selected: key === current }, t.mock.perspectives[key]),
    ),
  );
  select.addEventListener("change", () => onPerspective(select.value));
  return h(
    "section",
    { class: "mock-notice", "aria-label": t.mock.region },
    h(
      "div",
      { class: "mock-notice__inner" },
      h("p", { class: "mock-notice__text" }, t.mock.notice),
      h(
        "div",
        { class: "mock-notice__controls" },
        h("label", {}, h("span", { class: "mock-notice__label-text" }, t.mock.perspective), select),
        h("button", { type: "button", onclick: onReset }, t.mock.reset),
      ),
    ),
  );
}
