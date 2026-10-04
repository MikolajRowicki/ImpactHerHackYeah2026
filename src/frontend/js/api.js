import { OPERATIONS } from "./operations.js";

const MOCK_KEY = "mock";
const VARIANT_KEY = "variant";

export class ApiError extends Error {
  constructor(status, body) {
    const error = (body && body.error) || {};
    super(error.message || `HTTP ${status}`);
    this.status = status;
    this.code = error.code || "unknown";
    this.fields = error.fields || {};
  }
}

function attempt(fn) {
  try {
    return fn();
  } catch {
    return null;
  }
}

// ?mock=1 turns mock mode on, ?mock=0 turns it off; the choice stays in sessionStorage.
// ?variant=partner picks the example variant (get_me.200.partner.json); ?variant= clears it.
export function readMode(search, storage) {
  const params = new URLSearchParams(search);
  if (params.has(MOCK_KEY)) {
    const on = params.get(MOCK_KEY) === "1";
    attempt(() => (on ? storage.setItem(MOCK_KEY, "1") : storage.removeItem(MOCK_KEY)));
  }
  if (params.has(VARIANT_KEY)) {
    const value = params.get(VARIANT_KEY);
    attempt(() => (value ? storage.setItem(VARIANT_KEY, value) : storage.removeItem(VARIANT_KEY)));
  }
  const stored = (key) => attempt(() => storage.getItem(key));
  const mock = params.has(MOCK_KEY) ? params.get(MOCK_KEY) === "1" : stored(MOCK_KEY) === "1";
  const variant = params.has(VARIANT_KEY) ? params.get(VARIANT_KEY) : stored(VARIANT_KEY);
  return { mock, variant: variant || "" };
}

// Standalone (python -m http.server in the repo root): /src/frontend/index.html -> /contracts/examples/.
// Served by Django: /static/index.html -> /static/contracts/examples/.
export function examplesBase(pathname) {
  const marker = "/src/frontend/";
  const at = pathname.indexOf(marker);
  const root = at >= 0 ? pathname.slice(0, at + 1) : pathname.replace(/[^/]*$/, "");
  return `${root}contracts/examples/`;
}

// Operations that belong to the account, not to one group. They never carry `X-Group-Id`.
export const ACCOUNT_LEVEL = new Set([
  "health",
  "register",
  "login",
  "logout",
  "signup",
  "activate_account",
  "resend_activation",
  "request_password_reset",
  "confirm_password_reset",
  "change_password",
  "create_group",
  "get_invitation",
  "accept_invitation",
  "list_memberships",
  "delete_account",
  "get_help",
]);

function operation(operationId) {
  const found = OPERATIONS[operationId];
  if (!found) throw new Error(`Unknown operation: ${operationId}`);
  const [method, template, success] = found;
  return { method, template, success };
}

function fillPath(template, params = {}) {
  return template.replace(/\{(\w+)\}/g, (_, name) => {
    if (!(name in params)) throw new Error(`Missing path parameter: ${name}`);
    return encodeURIComponent(params[name]);
  });
}

// "?topic=hard_day" for { topic: "hard_day" }; nothing when there is no query.
function queryString(query) {
  const search = new URLSearchParams(query || {}).toString();
  return search ? `?${search}` : "";
}

function cookie(name, source) {
  const pair = source.split("; ").find((part) => part.startsWith(`${name}=`));
  return pair ? decodeURIComponent(pair.slice(name.length + 1)) : "";
}

async function readJson(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function liveAdapter({ fetchFn, getCookies }) {
  return async function call(operationId, { params, query, body, group } = {}) {
    const { method, template } = operation(operationId);
    const headers = { Accept: "application/json" };
    if (group) headers["X-Group-Id"] = String(group);
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (method !== "GET") {
      const token = cookie("csrftoken", getCookies());
      if (token) headers["X-CSRFToken"] = token;
    }
    const response = await fetchFn(fillPath(template, params) + queryString(query), {
      method,
      headers,
      credentials: "same-origin",
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const data = await readJson(response);
    if (!response.ok) throw new ApiError(response.status, data);
    return data;
  };
}

// Answers from contracts/examples and sends nothing to /api/v1.
// `status` asks for an error example, for example { status: 403 }.
function mockAdapter({ fetchFn, base, variant }) {
  return async function call(operationId, { status } = {}) {
    const { success } = operation(operationId);
    const code = status || success;
    const names = variant
      ? [`${operationId}.${code}.${variant}.json`, `${operationId}.${code}.json`]
      : [`${operationId}.${code}.json`];
    for (const name of names) {
      const response = await fetchFn(base + name);
      if (!response.ok) continue;
      const data = await readJson(response);
      if (code >= 400) throw new ApiError(code, data);
      return data;
    }
    throw new Error(`No example for ${operationId} with status ${code}`);
  };
}

export function createApi({
  mock,
  variant = "",
  base = "",
  fetchFn = (...args) => fetch(...args),
  getCookies = () => document.cookie,
}) {
  const adapter = mock
    ? mockAdapter({ fetchFn, base, variant })
    : liveAdapter({ fetchFn, getCookies });
  // The selected group travels with every call that works inside a group.
  let selected = null;
  return {
    mock,
    setGroup(id) {
      selected = id || null;
    },
    call(operationId, options = {}) {
      const group = ACCOUNT_LEVEL.has(operationId) ? null : selected;
      return adapter(operationId, { ...options, group });
    },
  };
}
