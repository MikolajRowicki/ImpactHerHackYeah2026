// Hash routes with named parameters, for example "/invite/:token".

function compile(pattern) {
  const keys = [];
  const source = pattern
    .split("/")
    .map((part) => {
      if (!part.startsWith(":")) return part.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      keys.push(part.slice(1));
      return "([^/]+)";
    })
    .join("/");
  return { regex: new RegExp(`^${source}$`), keys };
}

function decode(value) {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export function createRouter(routes) {
  const compiled = routes.map((route) => ({ route, ...compile(route.path) }));
  return function match(path) {
    for (const { route, regex, keys } of compiled) {
      const found = regex.exec(path);
      if (!found) continue;
      const params = Object.fromEntries(keys.map((key, i) => [key, decode(found[i + 1])]));
      return { route, params };
    }
    return null;
  };
}

export function currentPath() {
  const path = location.hash.replace(/^#/, "");
  return path.startsWith("/") ? path : path ? `/${path}` : "/";
}

// What the route allows this person to see.
// Returns "ok", "login" (needs a session), "home" (signed-in person on a signed-out page),
// or { reason } for the calm "not for you" screen.
export function guard(route, me) {
  if (route.access === "anyone") return "ok";
  if (route.access === "signed-out") return me ? "home" : "ok";
  if (!me) return "login";
  const membership = me.membership;
  const needsGroup = route.member || route.roles || route.statuses;
  if (needsGroup && !membership) return { reason: "noGroup" };
  if (route.roles && !route.roles.includes(membership.role)) {
    return { reason: route.roles.includes("woman") ? "motherOnly" : "lovedOnly" };
  }
  if (route.statuses && !route.statuses.includes(membership.group_status)) {
    return { reason: membership.group_status };
  }
  return "ok";
}
