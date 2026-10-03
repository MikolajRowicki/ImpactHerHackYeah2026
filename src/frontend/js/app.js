import { ApiError, createApi, examplesBase, readMode } from "./api.js";
import { createFrame, mockNotice } from "./frame.js";
import { clearMockState, createMockStore } from "./mock-store.js";
import { createRouter, currentPath, guard } from "./router.js";
import { checkIn } from "./screens/check-in.js";
import { group } from "./screens/group.js";
import { help } from "./screens/help.js";
import { invite } from "./screens/invite.js";
import { login, register } from "./screens/account.js";
import { notAllowed, notFound } from "./screens/not-found.js";
import { questions } from "./screens/questions.js";
import { start } from "./screens/start.js";
import { tasks } from "./screens/tasks.js";
import { createSession } from "./session.js";
import { errorState, loading } from "./ui/feedback.js";

// Who may open what: `access` (anyone, signed-out, signed-in), then `roles` and group `statuses`.
const ALL_ROLES = ["woman", "partner", "supporter"];
const match = createRouter([
  { path: "/", screen: start, access: "signed-in" },
  { path: "/login", screen: login, access: "signed-out" },
  { path: "/register", screen: register, access: "signed-out" },
  { path: "/check-in", screen: checkIn, roles: ["woman"], statuses: ["active", "closed"] },
  { path: "/questions", screen: questions, roles: ["partner", "supporter"], statuses: ["active"] },
  { path: "/tasks", screen: tasks, roles: ALL_ROLES, statuses: ["active", "closed"] },
  { path: "/group", screen: group, member: true },
  { path: "/invite/:token", screen: invite, access: "anyone" },
  { path: "/help", screen: help, access: "anyone" },
]);

function storage() {
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

const mode = readMode(location.search, storage());
const base = examplesBase(location.pathname);
if (!mode.mock) clearMockState(storage());
const api = mode.mock
  ? createMockStore({ base, storage: storage(), perspective: mode.variant })
  : createApi({ ...mode, base });
const session = createSession(api, storage());
const outlet = document.getElementById("screen");
const frame = createFrame({ onSignOut: signOut });

let shown = 0;

function navigate(path) {
  if (currentPath() === path) show();
  else location.hash = `#${path}`;
}

function render(node, { wide = false } = {}) {
  outlet.classList.toggle("screen--wide", wide);
  outlet.replaceChildren(node);
  window.scrollTo(0, 0);
  const heading = outlet.querySelector("h1");
  if (heading) {
    heading.setAttribute("tabindex", "-1");
    heading.focus({ preventScroll: true });
  }
}

async function show() {
  const ticket = ++shown;
  const stale = () => ticket !== shown;
  const path = currentPath();
  const found = match(path);
  if (!outlet.firstChild || !session.loaded) outlet.replaceChildren(loading());

  if (!session.loaded) {
    try {
      await session.load();
    } catch (error) {
      if (stale()) return;
      // Help and invitation previews still work when the session cannot be read.
      if (!found || found.route.access !== "anyone") {
        frame.update(null, path);
        render(errorState(error, show));
        return;
      }
    }
  }
  if (stale()) return;
  frame.update(session.me, path);
  if (!found) {
    render(notFound());
    return;
  }

  const verdict = guard(found.route, session.me);
  if (verdict === "login") {
    session.rememberPath(path);
    navigate("/login");
    return;
  }
  if (verdict === "home") {
    navigate("/");
    return;
  }
  if (verdict !== "ok") {
    render(notAllowed(verdict.reason));
    return;
  }

  const ctx = {
    api,
    session,
    params: found.params,
    navigate,
    refresh: show,
    // After sign-in, group changes and sign-out the person's role or group may differ.
    async reloadSession() {
      await session.load();
      await sessionChanged();
    },
    async setMe(me) {
      session.set(me);
      await sessionChanged();
    },
  };
  try {
    const node = await found.route.screen(ctx);
    if (stale()) return;
    render(node, { wide: Boolean(found.route.wide || node.dataset?.wide) });
  } catch (error) {
    if (stale()) return;
    if (error instanceof ApiError && error.status === 401) {
      session.clear();
      session.rememberPath(path);
      navigate("/login");
      return;
    }
    render(errorState(error, show));
  }
}

async function signOut() {
  try {
    await api.call("logout");
  } catch (error) {
    if (!(error instanceof ApiError && error.status === 401)) {
      render(errorState(error, signOut));
      return;
    }
  }
  session.clear();
  await showNotice();
  navigate("/login");
}

async function sessionChanged() {
  frame.update(session.me, currentPath());
  await showNotice();
}

async function showNotice() {
  if (!api.mock) return;
  document.getElementById("notice-slot").replaceChildren(
    mockNotice({
      current: await api.perspective(),
      async onPerspective(key) {
        await api.setPerspective(key);
        session.forget();
        await showNotice();
        navigate("/");
      },
      async onReset() {
        await api.reset();
        session.forget();
        await showNotice();
        navigate("/");
      },
    }),
  );
}

document.querySelector(".skip-link")?.addEventListener("click", (event) => {
  // The hash belongs to the router, so the skip link moves focus itself.
  event.preventDefault();
  const heading = outlet.querySelector("h1") || outlet;
  heading.setAttribute("tabindex", "-1");
  heading.focus();
});

window.addEventListener("hashchange", show);

// A link to the address already open fires no hashchange; it still means "show this afresh".
document.addEventListener("click", (event) => {
  const link = event.target.closest?.('a[href^="#/"]');
  if (link && link.getAttribute("href") === location.hash) show();
});

async function boot() {
  try {
    const params = new URLSearchParams(location.search);
    if (api.mock && params.has("variant")) {
      await api.setPerspective(mode.variant);
      // Applied once: a reload must keep the demo state, not sign the person in again.
      params.delete("variant");
      const query = params.toString() ? `?${params}` : "";
      history.replaceState(null, "", `${location.pathname}${query}${location.hash}`);
    }
    await showNotice();
  } finally {
    show();
  }
}

boot();
