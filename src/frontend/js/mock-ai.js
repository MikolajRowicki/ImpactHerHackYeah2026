// Sample answers of the two AI helpers for mock mode. The backend has the real rules: its crisis
// list is longer, and its guide comes from a model with sources from the curated file.

export const GUIDE_TOPICS = [
  "how_are_you",
  "offer_help",
  "listen_without_fixing",
  "hard_day",
  "suggest_professional_help",
];

// Folded like the backend: lowercase, no Polish diacritics, single spaces.
function fold(text) {
  return String(text)
    .toLowerCase()
    .replace(/ł/g, "l")
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

// A short sample of the backend's crisis phrases, enough to show the crisis answer in the demo.
const CRISIS = [
  "nie chce zyc",
  "nie chce juz zyc",
  "chce umrzec",
  "wolalabym umrzec",
  "wolalabym nie zyc",
  "chce zniknac",
  "zabic sie",
  "samobojst",
  "skrzywdzic sie",
  "skrzywdze dziecko",
  "skrzywdzic dziecko",
  "zrobie krzywde dziecku",
];

export function isCrisis(text) {
  const padded = ` ${fold(text)}`;
  return CRISIS.some((phrase) => padded.includes(` ${phrase}`));
}

// Two sample messages per recipient and tone, so "another suggestion" shows a change.
const MESSAGES = {
  "partner gentle": [
    "Ostatnio jest mi trudniej, niż pokazuję. Nie potrzebuję rad, wystarczy, że posiedzisz ze mną i mnie wysłuchasz. Dziękuję, że jesteś.",
    "Chcę Ci powiedzieć, że czuję się ostatnio bardzo zmęczona. Pomogłoby mi, gdybyśmy dziś wieczorem pobyli razem w spokoju.",
  ],
  "partner direct": [
    "Potrzebuję Twojej pomocy i mówię to wprost: jest mi ciężko. Usiądźmy dziś razem i ustalmy, co możesz wziąć na siebie w tym tygodniu.",
    "Jest mi teraz bardzo trudno. Proszę, przejmij jedną noc z dzieckiem, żebym mogła się wyspać.",
  ],
  "supporters gentle": [
    "Cieszę się, że jesteście blisko. Jest mi teraz trudniej, niż to widać. Bardzo pomogłaby mi krótka rozmowa albo ktoś, kto przejmie jedną małą rzecz.",
    "Dziękuję, że o mnie myślicie. Ostatnio mam mniej sił i chętnie przyjmę pomoc, nawet drobną.",
  ],
  "supporters direct": [
    "Potrzebuję wsparcia i wolę powiedzieć to jasno. Pomóżcie mi, proszę, w konkretnych sprawach: zakupy, posiłek albo godzina odpoczynku.",
    "Jest mi ciężko i potrzebuję pomocy. Czy ktoś z Was może w tym tygodniu przyjść na dwie godziny, żebym odpoczęła?",
  ],
};

export function sampleMessage(recipient, tone, turn) {
  const options = MESSAGES[`${recipient} ${tone}`];
  return options[turn % options.length];
}

const SOURCES = {
  pacjent: {
    title: "Młoda matka w depresji",
    url: "https://pacjent.gov.pl/jak-zyc-z-choroba/mloda-matka-w-depresji",
  },
  support: { title: "Depresja – jak wspierać chorych", url: "https://pacjent.gov.pl/node/2609" },
  mp: {
    title: "Depresja i psychoza poporodowa",
    url: "https://www.mp.pl/pacjent/psychiatria/choroby/91686,depresja-i-psychoza-poporodowa",
  },
  ministry: {
    title: "Gdzie uzyskać pomoc psychologiczną i psychiatryczną?",
    url: "https://www.gov.pl/web/zdrowie/gdzie-uzyskac-pomoc-psychologiczna-i-psychiatryczna",
  },
  words: {
    title: "Jak rozmawiać z osobą w depresji: co mówić najbliższej osobie, a jakich słów unikać?",
    url: "https://niewidacpomnie.org/2024/10/10/jak-rozmawiac-z-osoba-w-depresji-co-mowic-najblizszej-osobie-a-jakich-slow-unikac/",
  },
  sos: { title: "116sos.pl – pomoc psychologiczna dla osób dorosłych", url: "https://116sos.pl/" },
};

// The fixed lists match the backend's content/guide_topics.py; the opening lines alternate.
const GUIDE = {
  how_are_you: {
    opening: [
      [
        "Myślę o Tobie dziś. Jak się naprawdę czujesz?",
        "Mam chwilę tylko dla Ciebie. Opowiesz, jak minął Ci dzień?",
      ],
      [
        "Widzę, że dużo się teraz dzieje. Jak się masz, tak naprawdę?",
        "Jestem obok i mam czas. Powiesz mi, co u Ciebie?",
      ],
    ],
    avoid: ['Rad w stylu "weź się w garść".', "Porównywania z innymi mamami."],
    questions: ["Co dziś było najtrudniejsze?", "Co mogłoby Ci pomóc w najbliższych godzinach?"],
    sources: [SOURCES.pacjent, SOURCES.mp],
  },
  offer_help: {
    opening: [
      [
        "Chcę Ci dziś w czymś pomóc. Wybierz coś, co zdejmie Ci z głowy jedną rzecz.",
        "Mogę wziąć dziś dziecko na godzinę, żebyś odpoczęła. Kiedy Ci pasuje?",
      ],
      [
        "Powiedz, w czym konkretnie mogę Ci dziś pomóc.",
        "Zajmę się obiadem i zakupami, a Ty odpocznij, dobrze?",
      ],
    ],
    avoid: [
      'Zdania "daj znać, jakby coś", które zostawia całą pracę jej.',
      "Pomagania po swojemu bez zapytania, czego ona potrzebuje.",
    ],
    questions: ["Która rzecz z dzisiejszej listy waży najwięcej?", "Wolisz pomoc przy dziecku czy w domu?"],
    sources: [SOURCES.support, SOURCES.pacjent],
  },
  listen_without_fixing: {
    opening: [
      [
        "Nie musisz niczego rozwiązywać. Chcę po prostu posłuchać, co Ci leży na sercu.",
        "Jestem tu i mam czas. Powiedz, ile chcesz.",
      ],
      [
        "Nie będę dawać rad. Chcę Cię po prostu wysłuchać.",
        "Możesz mówić, ile chcesz, a ja jestem obok.",
      ],
    ],
    avoid: [
      "Przerywania i podsuwania gotowych rozwiązań.",
      'Zdań w stylu "inni mają gorzej" albo "nie przesadzaj".',
    ],
    questions: [
      "Jak to jest dla Ciebie?",
      "Czy potrzebujesz teraz raczej wysłuchania, czy pomysłu, co dalej?",
    ],
    sources: [SOURCES.words, SOURCES.support],
  },
  hard_day: {
    opening: [
      [
        "Widzę, że to był ciężki dzień. Jestem przy Tobie.",
        "To był trudny dzień i to w porządku, że tak się czujesz. Co mogę teraz zrobić?",
      ],
      [
        "Widzę, że dziś było Ci bardzo ciężko.",
        "Nie musisz niczego tłumaczyć. Jestem obok.",
      ],
    ],
    avoid: [
      'Mówienia, że "jutro będzie lepiej", zanim ona poczuje się wysłuchana.',
      "Oceniania, co zrobiła lub czego nie zdążyła.",
    ],
    questions: [
      "Co najbardziej Cię dziś wyczerpało?",
      "Czego potrzebujesz teraz: ciszy, przytulenia czy chwili dla siebie?",
    ],
    sources: [SOURCES.pacjent, SOURCES.words],
  },
  suggest_professional_help: {
    opening: [
      [
        "Martwię się o Ciebie, bo widzę, że od dłuższego czasu jest Ci ciężko. Czy możemy porozmawiać o tym, kto mógłby Ci pomóc?",
        "To, co czujesz, jest ważne. Lekarz albo psycholog może pomóc, a ja pójdę z Tobą, jeśli chcesz.",
      ],
      [
        "Widzę, że od dłuższego czasu jest Ci ciężko, i martwię się o Ciebie.",
        "Czy chcesz porozmawiać z lekarzem albo psychologiem? Mogę pomóc umówić wizytę.",
      ],
    ],
    avoid: [
      "Sugerowania, że coś jest z nią nie tak albo że sobie nie radzi.",
      "Stawiania diagnozy. Nie jesteśmy od tego, od tego jest lekarz.",
      "Naciskania, gdy ona nie jest gotowa. Wróć do tematu spokojnie za jakiś czas.",
    ],
    questions: [
      "Czy chciałabyś pomocy w znalezieniu numeru lub umówieniu wizyty?",
      "Co sprawia, że trudno Ci prosić o taką pomoc?",
    ],
    sources: [SOURCES.mp, SOURCES.ministry, SOURCES.sos],
  },
};

export function sampleGuide(topic, turn) {
  const guide = GUIDE[topic];
  return {
    topic,
    opening_lines: guide.opening[turn % guide.opening.length],
    avoid: guide.avoid,
    questions: guide.questions,
    source: "mock",
    sources: guide.sources,
  };
}
