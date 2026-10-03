// Every string the person reads lives here, never inside logic.
export const t = {
  appName: "MaydayMama",
  mockNotice: "Tryb demonstracyjny: widzisz przykładowe dane, nie prawdziwe.",
  home: {
    title: "Cześć",
    signedInAs: (name) => `Zalogowano jako ${name}.`,
    role: {
      woman: "Rola: mama",
      partner: "Rola: partner lub partnerka",
      supporter: "Rola: bliska osoba",
    },
    noGroup: "Nie należysz jeszcze do żadnej grupy.",
    signedOut: "Nie jesteś zalogowana ani zalogowany.",
    loading: "Wczytywanie…",
    failed: "Nie udało się wczytać danych. Spróbuj ponownie.",
  },
  notFound: {
    title: "Nie ma takiej strony",
    back: "Wróć na początek",
  },
};
