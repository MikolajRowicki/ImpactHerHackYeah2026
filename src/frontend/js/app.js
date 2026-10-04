import { ApiError, createApi, examplesBase, readMode } from "./api.js";
import { createFrame, mockNotice } from "./frame.js";
import { clearMockState, createMockStore } from "./mock-store.js";
import { createRouter, currentPath, guard } from "./router.js";
import { checkIn } from "./screens/check-in.js";
import { group } from "./screens/group.js";
import { education } from "./screens/education.js";
import { help } from "./screens/help.js";
import { invite } from "./screens/invite.js";
import { account, activate, forgot, login, register, reset } from "./screens/account.js";
import { notAllowed, notFound } from "./screens/not-found.js";
import { questions } from "./screens/questions.js";
import { sayIt } from "./screens/say-it.js";
import { start } from "./screens/start.js";
import { tasks } from "./screens/tasks.js";
import { groupPanel } from "./screens/panel.js";
import { createSession } from "./session.js";
import { openDialog } from "./ui/dialog.js";
import { errorState, loading } from "./ui/feedback.js";
import { t } from "./strings.pl.js";

// Who may open what: `access` (anyone, signed-out, signed-in), then `roles` and group `statuses`.
const ALL_ROLES = ["woman", "partner", "supporter"];
const match = createRouter([
  // A visitor sees the landing page here, a signed-in person their start.
  { path: "/", screen: start, access: "anyone" },
  { path: "/login", screen: login, access: "signed-out" },
  { path: "/register", screen: register, access: "signed-out" },
  { path: "/check-in", screen: checkIn, roles: ["woman"], statuses: ["active", "closed"] },
  { path: "/questions", screen: questions, roles: ["partner", "supporter"], statuses: ["active"] },
  { path: "/say-it", screen: sayIt, roles: ["woman"], statuses: ["active", "closed"] },
  { path: "/tasks", screen: tasks, roles: ALL_ROLES, statuses: ["active", "closed"] },
  { path: "/group", screen: group, member: true },
  { path: "/invite/:token", screen: invite, access: "anyone" },
  { path: "/education", screen: education, access: "signed-in" },
  { path: "/help", screen: help, access: "anyone" },
  { path: "/activate/:token", screen: activate, access: "anyone" },
  { path: "/forgot", screen: forgot, access: "anyone" },
  { path: "/reset/:token", screen: reset, access: "anyone" },
  { path: "/account", screen: account, access: "signed-in" },
]);

function storage() {
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

// The selected group is remembered in the browser, not only in the tab.
function remembered() {
  try {
    return window.localStorage;
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
const session = createSession(api, storage(), remembered());
const outlet = document.getElementById("screen");
const frame = createFrame({
  onSignOut: signOut,
  onSwitchGroup: switchGroup,
  onAddGroup: addGroup,
});

let shown = 0;

function makeCtx(params = {}) {
  return {
    api,
    session,
    params,
    navigate,
    refresh: show,
    // After sign-in, group changes and sign-out the person's role or group may differ.
    async reloadSession() {
      await session.load();
      await sessionChanged();
    },
    // The session ended without a sign-out call, for example after the account was deleted.
    async endSession() {
      session.clear();
      await showNotice();
      navigate("/");
    },
    // Reads the groups again and selects one the person just created or joined.
    async enterGroup(groupId) {
      await session.load(groupId);
      await sessionChanged();
    },
  };
}

async function switchGroup(groupId) {
  try {
    await session.load(groupId);
  } catch (error) {
    render(errorState(error, retry));
    return;
  }
  await sessionChanged();
  show();
}

// The panel of "what do you want to do" as a dialog, for a person who already has groups.
function addGroup() {
  openDialog({
    title: t.group.addGroupTitle,
    content: (close) =>
      groupPanel(makeCtx(), { onStarted: close }),
  });
}

function navigate(path) {
  if (currentPath() === path) show();
  else location.hash = `#${path}`;
}

function render(node, { wide = false } = {}) {
  outlet.removeAttribute("aria-busy");
  outlet.classList.toggle("screen--wide", wide);
  outlet.replaceChildren(node);
  window.scrollTo(0, 0);
  const heading = outlet.querySelector("h1");
  if (heading) {
    heading.setAttribute("tabindex", "-1");
    heading.focus({ preventScroll: true });
  }
}

// Answers that mean the person's membership changed elsewhere (removed, group started or
// closed by someone else), so the session must be read again.
const MEMBERSHIP_CODES = new Set(["not_a_member", "no_group", "group_pending", "group_closed"]);

// "Try again" reads the session again too, in case that is what changed.
function retry() {
  session.forget();
  show();
}

async function show() {
  const ticket = ++shown;
  const stale = () => ticket !== shown;
  const path = currentPath();
  const found = match(path);
  // Start depends most on the membership, so it always reads the session afresh.
  if (path === "/") session.forget();
  outlet.setAttribute("aria-busy", "true");
  outlet.replaceChildren(loading());

  if (!session.loaded) {
    try {
      await session.load();
    } catch (error) {
      if (stale()) return;
      // Help and invitation previews still work when the session cannot be read.
      // The start also needs the session: a visitor and a failed read look the same without it.
      if (!found || found.route.access !== "anyone" || path === "/") {
        // A failed read is not a sign-out: keep the frame of the person known so far.
        frame.update(session.me, path, session);
        render(errorState(error, retry));
        return;
      }
    }
  }
  if (stale()) return;
  frame.update(session.me, path, session);
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

  const ctx = makeCtx(found.params);
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
    if (error instanceof ApiError && MEMBERSHIP_CODES.has(error.code)) session.forget();
    render(errorState(error, retry));
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
  frame.update(session.me, currentPath(), session);
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
