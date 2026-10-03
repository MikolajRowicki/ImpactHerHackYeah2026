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
  return async function call(operationId, { params, body } = {}) {
    const { method, template } = operation(operationId);
    const headers = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (method !== "GET") {
      const token = cookie("csrftoken", getCookies());
      if (token) headers["X-CSRFToken"] = token;
    }
    const response = await fetchFn(fillPath(template, params), {
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
  const call = mock
    ? mockAdapter({ fetchFn, base, variant })
    : liveAdapter({ fetchFn, getCookies });
  return { mock, call };
}
