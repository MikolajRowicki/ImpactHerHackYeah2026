import { ApiError } from "./api.js";

const RETURN_KEY = "return-to";
const GROUP_KEY = "group-id";

// The signed-in person (the get_me answer for the selected group), or null when signed out.
// `remembered` is the storage that outlives the tab; the selected group lives there.
export function createSession(api, storage, remembered = null) {
  function readGroup() {
    try {
      const value = Number(remembered?.getItem(GROUP_KEY));
      return Number.isInteger(value) && value > 0 ? value : null;
    } catch {
      return null;
    }
  }

  function writeGroup(id) {
    try {
      if (id) remembered?.setItem(GROUP_KEY, String(id));
      else remembered?.removeItem(GROUP_KEY);
    } catch {
      // Without storage the earliest group is selected on the next visit.
    }
  }

  const session = {
    me: null,
    memberships: [],
    groupId: null,
    loaded: false,

    // Reads the person, then the groups. `prefer` is a group to select now (one just created or
    // joined). The group sent with `get_me` is only a guess until the list confirms it, so a
    // remembered group the person no longer belongs to is dropped and the answer read again.
    async load(prefer = null) {
      try {
        api.setGroup?.(prefer ?? session.groupId ?? readGroup());
        let me;
        try {
          me = await api.call("get_me");
        } catch (error) {
          if (!(error instanceof ApiError && error.code === "not_a_member")) throw error;
          api.setGroup?.(null);
          me = await api.call("get_me");
        }
        session.memberships = (await api.call("list_memberships")).items;
        session.select(prefer);
        const shown = me.membership?.group_id ?? null;
        session.me = shown === session.groupId ? me : await api.call("get_me");
      } catch (error) {
        if (!(error instanceof ApiError && error.status === 401)) throw error;
        session.me = null;
        session.memberships = [];
        session.groupId = null;
        api.setGroup?.(null);
      }
      session.loaded = true;
      return session.me;
    },

    // The group to work in: the wanted one, else the remembered one, else the earliest; only
    // ever one the person belongs to.
    select(wanted = null) {
      const ids = session.memberships.map((m) => m.group_id);
      const pick = [wanted, session.groupId, readGroup()].find((id) => ids.includes(id));
      session.groupId = pick ?? ids[0] ?? null;
      writeGroup(session.groupId);
      api.setGroup?.(session.groupId);
    },

    clear() {
      session.me = null;
      session.memberships = [];
      session.groupId = null;
      session.loaded = true;
      api.setGroup?.(null);
    },

    get selectedMembership() {
      return session.memberships.find((m) => m.group_id === session.groupId) || null;
    },

    get hasWomanGroup() {
      return session.memberships.some((m) => m.role === "woman");
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
