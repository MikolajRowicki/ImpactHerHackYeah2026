import { ApiError } from "../api.js";
import { h } from "../dom.js";
import { t } from "../strings.pl.js";

// Placeholder screen: shows who is signed in. Real screens replace it.
export async function home({ api }) {
  const section = h("section", {}, h("h1", {}, t.home.title));
  let me;
  try {
    me = await api.call("get_me");
  } catch (error) {
    const signedOut = error instanceof ApiError && error.status === 401;
    section.append(h("p", { class: "error" }, signedOut ? t.home.signedOut : t.home.failed));
    return section;
  }
  const card = h("div", { class: "card" }, h("p", {}, t.home.signedInAs(me.display_name)));
  card.append(
    h("p", { class: "muted" }, me.membership ? t.home.role[me.membership.role] : t.home.noGroup),
  );
  section.append(card);
  return section;
}
