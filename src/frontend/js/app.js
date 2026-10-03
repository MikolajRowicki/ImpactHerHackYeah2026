import { createApi, examplesBase, readMode } from "./api.js";
import { h } from "./dom.js";
import { home } from "./screens/home.js";
import { notFound } from "./screens/not-found.js";
import { t } from "./strings.pl.js";

const routes = { "/": home };

function storage() {
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

const mode = readMode(location.search, storage());
const api = createApi({ ...mode, base: examplesBase(location.pathname) });
const outlet = document.getElementById("screen");

if (api.mock) {
  document
    .getElementById("notice-slot")
    .replaceChildren(h("p", { class: "mock-notice", role: "status" }, t.mockNotice));
}

let shown = 0;

async function show() {
  const ticket = ++shown;
  const path = location.hash.replace(/^#/, "") || "/";
  const screen = routes[path] || notFound;
  const node = await screen({ api });
  if (ticket !== shown) return;
  outlet.replaceChildren(node);
}

window.addEventListener("hashchange", show);
show();
