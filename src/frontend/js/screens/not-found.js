import { h } from "../dom.js";
import { t } from "../strings.pl.js";

export function notFound() {
  return h(
    "section",
    {},
    h("h1", {}, t.notFound.title),
    h("p", {}, h("a", { href: "#/" }, t.notFound.back)),
  );
}
