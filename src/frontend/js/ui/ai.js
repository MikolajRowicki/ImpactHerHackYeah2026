import { h } from "../dom.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";

// Says where a generated text came from. Fixed texts (source "rules") carry no label.
export function originLabel(answer) {
  let text = null;
  if (answer.source === "groq") text = answer.sources?.length ? t.ai.byAiWithSources : t.ai.byAi;
  else if (answer.source === "mock") text = t.ai.sample;
  return text && h("p", { class: "origin-label" }, icon("sparkle", 16), text);
}

// "pacjent.gov.pl" for "https://pacjent.gov.pl/...".
export function siteName(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

// The pages a text was based on, as links that open in a new tab. Only https links are shown.
export function sourcesList(sources, headingId) {
  const safe = (sources || []).filter((source) => String(source.url).startsWith("https://"));
  if (safe.length === 0) return null;
  return h(
    "section",
    { class: "sources", "aria-labelledby": headingId },
    h("h3", { id: headingId }, t.talk.sourcesTitle),
    h(
      "ul",
      { class: "sources__list" },
      ...safe.map((source) =>
        h(
          "li",
          {},
          h(
            "a",
            { href: source.url, target: "_blank", rel: "noopener noreferrer" },
            source.title,
            h("span", { class: "visually-hidden" }, ` (${t.talk.opensInNewTab})`),
          ),
          h("span", { class: "sources__site" }, siteName(source.url)),
        ),
      ),
    ),
  );
}
