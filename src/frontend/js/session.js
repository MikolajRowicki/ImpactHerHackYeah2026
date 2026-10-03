import { ApiError } from "./api.js";

const RETURN_KEY = "return-to";

// The signed-in person (the get_me answer), or null when signed out.
export function createSession(api, storage) {
  const session = {
    me: null,
    loaded: false,

    async load() {
      try {
        session.me = await api.call("get_me");
      } catch (error) {
        if (!(error instanceof ApiError && error.status === 401)) throw error;
        session.me = null;
      }
      session.loaded = true;
      return session.me;
    },

    set(me) {
      session.me = me;
      session.loaded = true;
    },

    clear() {
      session.me = null;
      session.loaded = true;
    },

    forget() {
      session.loaded = false;
    },

    get role() {
      return session.me?.membership?.role || null;
    },

    get groupStatus() {
      return session.me?.membership?.group_status || null;
    },

    // The address a signed-out person wanted, kept for after sign-in.
    rememberPath(path) {
      try {
        storage?.setItem(RETURN_KEY, path);
      } catch {
        // Without storage the person lands on start after sign-in.
      }
    },

    // A new account has no group yet, so only an invitation is worth returning to.
    takeRememberedPath({ invitationsOnly = false } = {}) {
      let path = null;
      try {
        path = storage?.getItem(RETURN_KEY);
        storage?.removeItem(RETURN_KEY);
      } catch {
        path = null;
      }
      const safe = path && path.startsWith("/") && !/^\/(login|register)\b/.test(path);
      if (!safe || (invitationsOnly && !path.startsWith("/invite/"))) return "/";
      return path;
    },
  };
  return session;
}
