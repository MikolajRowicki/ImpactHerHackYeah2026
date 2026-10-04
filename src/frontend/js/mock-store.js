import { ACCOUNT_LEVEL, ApiError } from "./api.js";
import { OPERATIONS } from "./operations.js";
import { t } from "./strings.pl.js";

// Mock mode with memory: answers start from contracts/examples, and what the person changes
// during the demo is kept in sessionStorage for the browser tab. Nothing goes to /api/v1.
// The rules the backend enforces are mirrored here with the matching contract error examples.

const STATE_KEY = "mock-state";
const VERSION = 2;
export const DEMO_PASSWORD = "tajne-haslo-123";
export const PERSPECTIVES = ["woman", "partner", "supporter", "no_group", "pending", "both"];

// The perspectives are separate people: the mother, her partner and a supporter in one active
// group, someone without a group, a partner whose group waits for the mother, and a person who
// is the mother of her own group and a supporter in Ewa's.
const PERSON_OF = { woman: 1, partner: 2, supporter: 3, no_group: 101, pending: 102, both: 103 };
const EWA = 104;
const ACTIVE_GROUP = 1;
const PENDING_GROUP = 2;
const OWN_GROUP = 3;
const EWAS_GROUP = 4;

const STATUS_ORDER = { open: 0, claimed: 1, done: 2 };
const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const ENUMS = {
  mood: ["good", "okay", "low", "very_low"],
  sleep: ["enough", "little", "almost_none"],
  anxiety: ["none", "some", "strong"],
};

const now = () => new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
const copy = (value) => JSON.parse(JSON.stringify(value));

function randomToken() {
  const bytes = crypto.getRandomValues(new Uint8Array(12));
  return Array.from(bytes, (b) => "abcdefghjkmnpqrstuvwxyz23456789"[b % 31]).join("");
}

export function clearMockState(storage) {
  try {
    storage?.removeItem(STATE_KEY);
  } catch {
    // Nothing stored, nothing to clear.
  }
}

export function createMockStore({ base, storage, perspective = "", fetchFn = (...a) => fetch(...a) }) {
  const examples = new Map();
  let memory = null;
  let selected = null;

  function example(name) {
    if (!examples.has(name)) {
      examples.set(
        name,
        fetchFn(base + name).then((response) => (response.ok ? response.json() : null)),
      );
    }
    return examples.get(name).then((value) => (value === null ? null : copy(value)));
  }

  // Throws the first error example that exists among `names`.
  async function refuse(status, ...names) {
    for (const name of names) {
      const body = await example(name);
      if (body) throw new ApiError(status, body);
    }
    throw new ApiError(status, null);
  }

  function invalid(fields) {
    const body = { error: { code: "validation_error", message: t.mock.errors.validation, fields } };
    return Promise.reject(new ApiError(422, body));
  }

  function load() {
    try {
      const raw = storage?.getItem(STATE_KEY);
      if (raw) {
        const state = JSON.parse(raw);
        if (state.version === VERSION) return state;
      }
    } catch {
      // Broken or unavailable storage falls back to memory below.
    }
    return memory;
  }

  function save(state) {
    memory = state;
    try {
      storage?.setItem(STATE_KEY, JSON.stringify(state));
    } catch {
      // Memory keeps the demo going for this page.
    }
  }

  async function seed(start) {
    const [anna, piotr, marta, alone, waiting, members, tasks, checkIns, group, invitation] =
      await Promise.all(
        [
          "get_me.200.json",
          "get_me.200.partner.json",
          "get_me.200.supporter.json",
          "get_me.200.no_group.json",
          "get_me.200.pending.json",
          "list_members.200.json",
          "list_tasks.200.json",
          "list_check_ins.200.json",
          "get_group.200.json",
          "get_invitation.200.json",
        ].map(example),
      );
    const joined = (id) => members.items.find((m) => m.id === id)?.joined_at || group.created_at;
    const person = (key, me, groupId) => ({
      key,
      id: PERSON_OF[key],
      email: me.email,
      display_name: me.display_name,
      password: DEMO_PASSWORD,
      memberships: groupId
        ? [{ group_id: groupId, role: me.membership.role, joined_at: joined(PERSON_OF[key]) }]
        : [],
    });
    const ola = {
      ...person("both", marta, null),
      email: "julia@example.com",
      display_name: "Julia",
      memberships: [
        { group_id: OWN_GROUP, role: "woman", joined_at: group.created_at },
        { group_id: EWAS_GROUP, role: "supporter", joined_at: joined(PERSON_OF.supporter) },
      ],
    };
    const ewa = {
      key: null,
      id: EWA,
      email: "ewa@example.com",
      display_name: "Ewa",
      password: DEMO_PASSWORD,
      memberships: [{ group_id: EWAS_GROUP, role: "woman", joined_at: group.created_at }],
    };
    const created = await example("create_invitation.201.json");
    return {
      version: VERSION,
      signedIn: true,
      current: PERSON_OF[start] || PERSON_OF.woman,
      nextId: 1000,
      people: [
        person("woman", anna, ACTIVE_GROUP),
        person("partner", piotr, ACTIVE_GROUP),
        person("supporter", marta, ACTIVE_GROUP),
        person("no_group", alone, null),
        person("pending", waiting, PENDING_GROUP),
        ola,
        ewa,
      ],
      groups: [
        { id: ACTIVE_GROUP, status: group.status, created_at: group.created_at },
        { id: PENDING_GROUP, status: "pending", created_at: group.created_at },
        { id: OWN_GROUP, status: "active", created_at: group.created_at },
        { id: EWAS_GROUP, status: "active", created_at: group.created_at },
      ],
      tasks: tasks.items.map((task) => ({ ...task, group_id: ACTIVE_GROUP })),
      checkIns: checkIns.items.map((item) => ({ ...item, person_id: PERSON_OF.woman })),
      invitations: [
        {
          token: created.token,
          group_id: ACTIVE_GROUP,
          role: invitation.role,
          invited_by: PERSON_OF.woman,
          created_at: created.created_at,
          expires_at: invitation.expires_at,
          used: false,
        },
      ],
      observations: 0,
    };
  }

  async function state() {
    let current = load();
    if (!current) {
      const fresh = await seed(perspective);
      current = load();
      if (!current) {
        save(fresh);
        current = fresh;
      }
    }
    return current;
  }

  // Views in the exact shapes of the contract.
  const findGroup = (s, id) => s.groups.find((g) => g.id === id);
  const groupOf = (s, membership) => membership && findGroup(s, membership.group_id);
  const memberOf = (person, groupId) => person.memberships.find((m) => m.group_id === groupId);
  // The earliest membership is the one used when no group is named, as in the backend.
  const earliest = (person) =>
    [...person.memberships].sort(
      (a, b) => a.joined_at.localeCompare(b.joined_at) || a.group_id - b.group_id,
    )[0] || null;
  const meView = (s, person, membership) => ({
    id: person.id,
    email: person.email,
    display_name: person.display_name,
    membership: membership
      ? {
          group_id: membership.group_id,
          role: membership.role,
          group_status: groupOf(s, membership).status,
        }
      : null,
  });
  const womanOf = (s, groupId) =>
    s.people.find((p) => memberOf(p, groupId)?.role === "woman") || null;
  const groupView = (group, role) => ({
    id: group.id,
    status: group.status,
    my_role: role,
    created_at: group.created_at,
  });
  const taskView = ({ group_id: _, ...task }) => task;
  const personRef = (person) => ({ id: person.id, display_name: person.display_name });
  const nextId = (s) => ++s.nextId;

  function requireActive(op, group) {
    if (group.status === "pending") return refuse(409, "create_task.409.json");
    if (group.status === "closed") {
      return refuse(409, `${op}.409.closed.json`, "claim_task.409.closed.json");
    }
    return null;
  }

  function mail(s, kind, email) {
    s.outbox = s.outbox || [];
    s.outbox.push({ kind, email, token: randomToken(), used: false });
  }

  function takeMail(s, kind, token) {
    const letter = (s.outbox || []).find((m) => m.kind === kind && m.token === token && !m.used);
    if (letter) letter.used = true;
    return letter;
  }

  function findTask(s, group, id) {
    return s.tasks.find((task) => task.group_id === group.id && task.id === Number(id));
  }

  // Each handler changes the state synchronously and returns the answer, or a rejected promise.
  // Refusals come before any change, so a refused call leaves the state as it was.
  const handlers = {
    health: () => ({ status: "ok" }),

    register(s, _me, { body = {} }) {
      const email = String(body.email || "").trim().toLowerCase();
      const fields = {};
      if (!String(body.display_name || "").trim()) fields.display_name = t.mock.errors.nameMissing;
      if (String(body.password || "").length < 8) fields.password = t.mock.errors.passwordShort;
      if (Object.keys(fields).length) return invalid(fields);
      if (!EMAIL.test(email)) return refuse(422, "login.422.json");
      if (s.people.some((p) => p.email === email)) return refuse(422, "register.422.json");
      const person = {
        key: null,
        id: nextId(s),
        email,
        display_name: String(body.display_name).trim(),
        password: String(body.password),
        memberships: [],
      };
      s.people.push(person);
      s.signedIn = true;
      s.current = person.id;
      return meView(s, person, null);
    },

    login(s, _me, { body = {} }) {
      const email = String(body.email || "").trim().toLowerCase();
      const person = s.people.find((p) => p.email === email && p.password === body.password);
      if (!person || person.inactive) return refuse(401, "login.401.json");
      s.signedIn = true;
      s.current = person.id;
      return meView(s, person, earliest(person));
    },

    logout(s) {
      s.signedIn = false;
      return { status: "ok" };
    },

    get_me: (s, me, _opts, _group, membership) => meView(s, me, membership),

    list_memberships(s, me) {
      const items = [...me.memberships]
        .sort((a, b) => a.joined_at.localeCompare(b.joined_at) || a.group_id - b.group_id)
        .map((m) => ({
          group_id: m.group_id,
          role: m.role,
          group_status: findGroup(s, m.group_id).status,
          woman_name: womanOf(s, m.group_id)?.display_name ?? null,
        }));
      return { items };
    },

    create_group(s, me, { body = {} }) {
      if (!["woman", "partner"].includes(body.role)) return refuse(422, "create_group.422.json");
      const waiting = me.memberships.some(
        (m) => m.role === "partner" && findGroup(s, m.group_id).status === "pending",
      );
      const isMother = me.memberships.some((m) => m.role === "woman");
      if ((body.role === "woman" && isMother) || (body.role === "partner" && waiting)) {
        return refuse(409, "create_group.409.json");
      }
      const group = {
        id: nextId(s),
        status: body.role === "woman" ? "active" : "pending",
        created_at: now(),
      };
      s.groups.push(group);
      me.memberships.push({ group_id: group.id, role: body.role, joined_at: group.created_at });
      return groupView(group, body.role);
    },

    get_group(s, me, _opts, _group, membership) {
      if (!membership) return refuse(404, "get_group.404.json");
      return groupView(groupOf(s, membership), membership.role);
    },

    close_group(s, me, _opts, group, membership) {
      if (membership.role !== "woman") return refuse(403, "close_group.403.json");
      group.status = "closed";
      return groupView(group, "woman");
    },

    list_members(s, _me, _opts, group) {
      const items = s.people
        .filter((p) => memberOf(p, group.id))
        .map((p) => ({ person: p, membership: memberOf(p, group.id) }))
        .sort((a, b) => a.membership.joined_at.localeCompare(b.membership.joined_at))
        .map(({ person, membership }) => ({
          id: person.id,
          display_name: person.display_name,
          role: membership.role,
          joined_at: membership.joined_at,
        }));
      return { items };
    },

    remove_member(s, me, { params = {} }, group, membership) {
      if (membership.role !== "woman") return refuse(403, "remove_member.403.json");
      const target = s.people.find(
        (p) => p.id === Number(params.member_id) && memberOf(p, group.id),
      );
      if (!target) return refuse(404, "remove_member.404.json");
      if (target.id === me.id) return refuse(409, "remove_member.409.json");
      target.memberships = target.memberships.filter((m) => m.group_id !== group.id);
      return { status: "ok" };
    },

    leave_group(s, me, _opts, group, membership) {
      if (membership.role === "woman" && group.status !== "closed") {
        return refuse(409, "leave_group.409.json");
      }
      if (membership.role === "woman") {
        // She closed it and walks away: the group goes with its people's memberships.
        s.people.forEach((p) => {
          p.memberships = p.memberships.filter((m) => m.group_id !== group.id);
        });
        s.groups = s.groups.filter((g) => g.id !== group.id);
        s.tasks = s.tasks.filter((task) => task.group_id !== group.id);
        s.invitations = s.invitations.filter((i) => i.group_id !== group.id);
      } else {
        me.memberships = me.memberships.filter((m) => m.group_id !== group.id);
      }
      return { status: "ok" };
    },

    list_invitations(s, me, _opts, group, membership) {
      const manages =
        membership.role === "woman" ||
        (membership.role === "partner" && group.status === "pending");
      if (!manages) return refuse(403, "list_invitations.403.json");
      const items = s.invitations
        .filter((i) => i.group_id === group.id && !i.used && !i.revoked)
        .sort((a, b) => b.created_at.localeCompare(a.created_at))
        .map(({ token, role, created_at, expires_at }) => ({ token, role, created_at, expires_at }));
      return { items };
    },

    revoke_invitation(s, me, { params = {} }, group, membership) {
      const manages =
        membership.role === "woman" ||
        (membership.role === "partner" && group.status === "pending");
      if (!manages) return refuse(403, "revoke_invitation.403.json");
      const invitation = s.invitations.find(
        (i) => i.group_id === group.id && i.token === params.token && !i.used && !i.revoked,
      );
      if (!invitation) return refuse(404, "revoke_invitation.404.json");
      invitation.revoked = true;
      return { status: "ok" };
    },

    delete_account(s, me) {
      // A mother takes her group with her; elsewhere only the person's memberships go.
      for (const membership of [...me.memberships]) {
        if (membership.role === "woman") {
          s.people.forEach((p) => {
            p.memberships = p.memberships.filter((m) => m.group_id !== membership.group_id);
          });
          s.groups = s.groups.filter((g) => g.id !== membership.group_id);
        }
      }
      s.people = s.people.filter((p) => p.id !== me.id);
      s.signedIn = false;
      return { status: "ok" };
    },

    create_invitation(s, me, { body = {} }, group, membership) {
      if (group.status === "closed") return refuse(409, "create_invitation.409.json");
      const role = membership.role;
      const allowed =
        role === "woman"
          ? ["partner", "supporter"]
          : role === "partner" && group.status === "pending"
            ? ["woman"]
            : [];
      if (!allowed.includes(body.role)) return refuse(403, "create_invitation.403.json");
      if (body.email && !EMAIL.test(body.email)) return refuse(422, "create_invitation.422.json");
      const created = now();
      const invitation = {
        token: randomToken(),
        group_id: group.id,
        role: body.role,
        invited_by: me.id,
        created_at: created,
        expires_at: new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString().replace(/\.\d{3}Z$/, "Z"),
        used: false,
      };
      s.invitations.push(invitation);
      const { token, expires_at } = invitation;
      return { token, role: body.role, created_at: created, expires_at };
    },

    get_invitation(s, _me, { params = {} }) {
      const invitation = s.invitations.find((i) => i.token === params.token && !i.used && !i.revoked);
      if (!invitation) return refuse(404, "get_invitation.404.json");
      const inviter = s.people.find((p) => p.id === invitation.invited_by);
      return {
        role: invitation.role,
        invited_by_name: inviter.display_name,
        group_status: findGroup(s, invitation.group_id).status,
        expires_at: invitation.expires_at,
      };
    },

    accept_invitation(s, me, { params = {} }) {
      const invitation = s.invitations.find((i) => i.token === params.token && !i.used && !i.revoked);
      if (!invitation) return refuse(404, "accept_invitation.404.json");
      const group = findGroup(s, invitation.group_id);
      if (group.status === "closed") return refuse(409, "accept_invitation.409.closed.json");
      const alreadyMother = invitation.role === "woman" && me.memberships.some((m) => m.role === "woman");
      if (memberOf(me, group.id) || alreadyMother) return refuse(409, "accept_invitation.409.json");
      const membership = { group_id: group.id, role: invitation.role, joined_at: now() };
      me.memberships.push(membership);
      if (invitation.role === "woman" && group.status === "pending") group.status = "active";
      invitation.used = true;
      return meView(s, me, membership);
    },

    create_check_in(s, me, { body = {} }, group, membership) {
      if (membership.role !== "woman") return refuse(403, "create_check_in.403.json");
      const blocked = requireActive("create_check_in", group);
      if (blocked) return blocked;
      const fields = {};
      for (const [name, values] of Object.entries(ENUMS)) {
        if (!values.includes(body[name])) fields[name] = t.mock.errors.pickOne;
      }
      if (Object.keys(fields).length) return invalid(fields);
      const entry = {
        id: nextId(s),
        created_at: now(),
        mood: body.mood,
        sleep: body.sleep,
        anxiety: body.anxiety,
      };
      s.checkIns.push({ ...entry, person_id: me.id });
      return entry;
    },

    list_check_ins(s, me, _opts, _group, membership) {
      if (membership.role !== "woman") return refuse(403, "list_check_ins.403.json");
      const items = s.checkIns
        .filter((entry) => entry.person_id === me.id)
        .sort((a, b) => b.created_at.localeCompare(a.created_at) || b.id - a.id)
        .map(({ person_id: _, ...entry }) => entry);
      return { items };
    },

    list_observation_questions(s, me, _opts, _group, membership) {
      if (membership.role === "woman") return refuse(403, "list_observation_questions.403.json");
      return example("list_observation_questions.200.json");
    },

    create_observation(s, me, { body = {} }, group, membership) {
      if (membership.role === "woman") return refuse(403, "create_observation.403.json");
      const blocked = requireActive("create_observation", group);
      if (blocked) return blocked;
      if (!Array.isArray(body.answers) || body.answers.length === 0) {
        return refuse(422, "create_observation.422.json");
      }
      // Answers are only counted: the demo never shows them back, like the real backend.
      s.observations += 1;
      return { id: nextId(s), created_at: now() };
    },

    get_summary(s, me, _opts, _group, membership) {
      const role = membership.role;
      return example(role === "woman" ? "get_summary.200.json" : `get_summary.200.${role}.json`);
    },

    list_tasks(s, _me, _opts, group) {
      const items = s.tasks
        .filter((task) => task.group_id === group.id)
        .sort((a, b) => STATUS_ORDER[a.status] - STATUS_ORDER[b.status] || b.id - a.id)
        .map(taskView);
      return { items };
    },

    create_task(s, me, { body = {} }, group) {
      const blocked = requireActive("create_task", group);
      if (blocked) return blocked;
      const title = String(body.title || "").trim();
      const details = String(body.details || "").trim();
      if (!title || title.length > 120) return refuse(422, "create_task.422.json");
      if (details.length > 500) return invalid({ details: t.mock.errors.detailsLong });
      const task = {
        id: nextId(s),
        title,
        details: details || null,
        status: "open",
        created_by: personRef(me),
        claimed_by: null,
        created_at: now(),
        completed_at: null,
        group_id: group.id,
      };
      s.tasks.push(task);
      return taskView(task);
    },

    claim_task(s, me, { params = {} }, group) {
      const blocked = requireActive("claim_task", group);
      if (blocked) return blocked;
      const task = findTask(s, group, params.task_id);
      if (!task) return refuse(404, "claim_task.404.json");
      if (task.status !== "open") return refuse(409, "claim_task.409.json");
      task.status = "claimed";
      task.claimed_by = personRef(me);
      return taskView(task);
    },

    complete_task(s, me, { params = {} }, group) {
      const blocked = requireActive("complete_task", group);
      if (blocked) return blocked;
      const task = findTask(s, group, params.task_id);
      if (!task) return refuse(404, "complete_task.404.json");
      if (task.status !== "claimed") return refuse(409, "complete_task.409.json");
      if (task.claimed_by.id !== me.id) return refuse(403, "complete_task.403.json");
      task.status = "done";
      task.completed_at = now();
      return taskView(task);
    },

    // Account security. Answers never tell whether an address has an account; the "e-mails"
    // land in a demo outbox that the screens can show in mock mode.
    signup(s, _me, { body = {} }) {
      const email = String(body.email || "").trim().toLowerCase();
      const fields = {};
      if (!String(body.display_name || "").trim()) fields.display_name = t.mock.errors.nameMissing;
      if (String(body.password || "").length < 8) fields.password = t.mock.errors.passwordShort;
      if (Object.keys(fields).length) return invalid(fields);
      if (!EMAIL.test(email)) return refuse(422, "resend_activation.422.json");
      if (!s.people.some((p) => p.email === email)) {
        s.people.push({
          key: null,
          id: nextId(s),
          email,
          display_name: String(body.display_name).trim(),
          password: String(body.password),
          memberships: [],
          inactive: true,
        });
        mail(s, "activate", email);
      }
      return { status: "ok" };
    },

    activate_account(s, _me, { body = {} }) {
      const letter = takeMail(s, "activate", body.token);
      if (!letter) return refuse(404, "activate_account.404.json");
      const person = s.people.find((p) => p.email === letter.email);
      if (person) person.inactive = false;
      return { status: "ok" };
    },

    resend_activation(s, _me, { body = {} }) {
      const email = String(body.email || "").trim().toLowerCase();
      if (!EMAIL.test(email)) return refuse(422, "resend_activation.422.json");
      if (s.people.some((p) => p.email === email && p.inactive)) mail(s, "activate", email);
      return { status: "ok" };
    },

    request_password_reset(s, _me, { body = {} }) {
      const email = String(body.email || "").trim().toLowerCase();
      if (!EMAIL.test(email)) return refuse(422, "request_password_reset.422.json");
      if (s.people.some((p) => p.email === email)) mail(s, "reset", email);
      return { status: "ok" };
    },

    confirm_password_reset(s, _me, { body = {} }) {
      const letter = (s.outbox || []).find(
        (m) => m.kind === "reset" && m.token === body.token && !m.used,
      );
      if (!letter) return refuse(404, "confirm_password_reset.404.json");
      // A weak password keeps the link usable, like the backend.
      if (String(body.password || "").length < 8) return refuse(422, "confirm_password_reset.422.json");
      letter.used = true;
      const person = s.people.find((p) => p.email === letter.email);
      if (person) person.password = String(body.password);
      return { status: "ok" };
    },

    change_password(s, me, { body = {} }) {
      if (body.current_password !== me.password) return refuse(422, "change_password.422.json");
      if (String(body.new_password || "").length < 8) {
        return invalid({ new_password: t.mock.errors.passwordShort });
      }
      me.password = String(body.new_password);
      return { status: "ok" };
    },

    release_task(s, me, { params = {} }, group) {
      const blocked = requireActive("release_task", group);
      if (blocked) return blocked;
      const task = findTask(s, group, params.task_id);
      if (!task) return refuse(404, "release_task.404.json");
      if (task.status !== "claimed") return refuse(409, "release_task.409.json");
      if (task.claimed_by.id !== me.id) return refuse(403, "release_task.403.json");
      task.status = "open";
      task.claimed_by = null;
      return taskView(task);
    },

    list_self_care(s, me, _opts, _group, membership) {
      if (membership.role !== "woman") return refuse(403, "list_self_care.403.json");
      return example("list_self_care.200.json");
    },
  };

  const ANYONE = new Set([
    "health",
    "register",
    "login",
    "get_invitation",
    "signup",
    "activate_account",
    "resend_activation",
    "request_password_reset",
    "confirm_password_reset",
  ]);
  const SIGNED_IN = new Set([
    "logout",
    "get_me",
    "list_memberships",
    "create_group",
    "get_group",
    "accept_invitation",
    "change_password",
    "delete_account",
  ]);

  async function call(operationId, options = {}) {
    if (!OPERATIONS[operationId]) throw new Error(`Unknown operation: ${operationId}`);
    await state();
    // From here to save() nothing is awaited, so two calls never interleave their changes.
    const s = load();
    const me = s.signedIn ? s.people.find((p) => p.id === s.current) : null;
    // The named group, like the `X-Group-Id` header of the real API.
    const named = ACCOUNT_LEVEL.has(operationId) ? null : (options.group ?? selected);
    const membership = !me ? null : named ? memberOf(me, Number(named)) || null : earliest(me);
    let answer;
    if (!ANYONE.has(operationId) && !me) {
      answer = refuse(401, `${operationId}.401.json`, "get_me.401.json");
    } else if (named && !membership && !ANYONE.has(operationId) && operationId !== "list_memberships") {
      // A group the person does not belong to is refused, whatever the operation.
      answer = refuse(403, "list_members.403.json");
    } else if (ANYONE.has(operationId) || SIGNED_IN.has(operationId)) {
      answer = handlers[operationId](s, me, options, membership && groupOf(s, membership), membership);
    } else if (!membership) {
      answer = refuse(403, "list_tasks.403.json");
    } else {
      answer = handlers[operationId](s, me, options, groupOf(s, membership), membership);
    }
    save(s);
    return copy(await answer);
  }

  return {
    mock: true,
    call,

    setGroup(id) {
      selected = id || null;
    },

    async perspective() {
      const s = await state();
      if (!s.signedIn) return "";
      return s.people.find((p) => p.id === s.current)?.key || "other";
    },

    async setPerspective(key) {
      await state();
      const s = load();
      s.signedIn = true;
      s.current = PERSON_OF[key] || PERSON_OF.woman;
      save(s);
    },

    // The newest unused demo e-mail of a kind for an address, so mock mode can show its link.
    async lastMail(kind, email) {
      const s = await state();
      const address = String(email || "").trim().toLowerCase();
      const letters = (s.outbox || []).filter(
        (m) => m.kind === kind && m.email === address && !m.used,
      );
      return letters.at(-1) || null;
    },

    async reset() {
      const keep = await this.perspective();
      clearMockState(storage);
      memory = null;
      if (PERSPECTIVES.includes(keep)) perspective = keep;
      await state();
    },
  };
}
