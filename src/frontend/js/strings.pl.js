// Every string the person reads lives here, never inside logic. One key per area.
export const t = {
  common: {
    appName: "MaydayMama",
    skipLink: "Przejdź do treści",
    loading: "Wczytywanie…",
    failedTitle: "Coś poszło nie tak",
    failed: "Nie udało się wczytać danych. Spróbuj ponownie.",
    actionFailed: "Nie udało się. Spróbuj ponownie za chwilę.",
    retry: "Spróbuj ponownie",
    backHome: "Wróć na start",
    cancel: "Anuluj",
    close: "Zamknij",
    roles: {
      woman: "Mama",
      partner: "Partner lub partnerka",
      supporter: "Bliska osoba",
    },
  },

  nav: {
    label: "Nawigacja",
    start: "Start",
    checkIn: "Mój dzień",
    questions: "Pytania",
    tasks: "Zadania",
    group: "Grupa",
    help: "Pomoc",
    login: "Zaloguj się",
    signOut: "Wyloguj",
  },

  theme: {
    dark: "Ciemny motyw",
  },

  shell: {
    notFoundTitle: "Nie ma takiej strony",
    notFoundText: "Ten adres nigdzie nie prowadzi. Może link był niepełny.",
    notFoundBack: "Wróć na początek",
    notAllowedTitle: "To miejsce jest dla kogoś innego",
    notAllowed: {
      motherOnly: "To miejsce należy do mamy. Tylko ona widzi tu swoje wpisy.",
      lovedOnly: "Te pytania są dla bliskich osób mamy. Ty masz swoje miejsce na start.",
      noGroup: "To miejsce otworzy się, gdy dołączysz do grupy albo ją założysz.",
      pending: "Grupa zacznie działać, gdy mama przyjmie zaproszenie. Do tego czasu to miejsce jest puste.",
      closed: "Ta grupa została zamknięta, więc to miejsce nie przyjmuje już nowych odpowiedzi.",
    },
  },

  help: {
    title: "Pomoc",
    lead: "Tu będzie spokojne miejsce z kontaktami do wsparcia, gdy jest trudno.",
    comingTitle: "Kontakty pojawią się wkrótce",
    coming:
      "Sprawdzamy je starannie, zanim je tu pokażemy. Wolimy nie podawać niczego, czego nie jesteśmy pewni.",
    notADoctorTitle: "MaydayMama nie zastępuje lekarza",
    notADoctor:
      "Aplikacja niczego nie diagnozuje. Pomaga zauważyć zmiany i podzielić się codziennymi obowiązkami.",
    talkTitle: "Nie musisz zostawać z tym w pojedynkę",
    talk: "Jeśli coś Cię niepokoi, porozmawiaj z kimś, komu ufasz: z bliską osobą, położną albo lekarzem.",
  },

  mock: {
    notice: "Tryb demonstracyjny: widzisz przykładowe dane, nie prawdziwe.",
    region: "Tryb demonstracyjny",
    perspective: "Pokaż jako",
    perspectives: {
      woman: "Mama (Anna)",
      partner: "Partner (Piotr)",
      supporter: "Bliska osoba (Marta)",
      no_group: "Osoba bez grupy",
      pending: "Grupa czeka na mamę",
    },
    signedOut: "Nikt (wylogowano)",
    other: "Konto założone w demo",
    reset: "Zacznij demo od nowa",
    loginHint: (email, password) => `W demo zaloguj się jako ${email}, hasło: ${password}.`,
    errors: {
      validation: "Popraw zaznaczone pola.",
      pickOne: "Wybierz jedną z odpowiedzi.",
      passwordShort: "Hasło musi mieć co najmniej 8 znaków.",
      nameMissing: "Wpisz, jak mamy się do Ciebie zwracać.",
      detailsLong: "Opis może mieć najwyżej 500 znaków.",
    },
  },

  summary: {
    title: "Ogólny obraz",
    trend: {
      stable: {
        woman: "Ostatnie dni wyglądają spokojnie. Tak trzymaj, w swoim tempie.",
        loved: "Ostatnie dni wyglądają u niej spokojnie.",
      },
      uncertain: {
        woman: "Ostatnie dni były różne. Przyglądamy się temu z uwagą i spokojem.",
        loved: "Ostatnie dni były u niej różne. Przyglądamy się temu z uwagą i spokojem.",
      },
      needs_attention: {
        woman: "Wygląda na to, że ostatnio jest Ci trudniej. Nie musisz radzić sobie z tym sama.",
        loved: "Wygląda na to, że ostatnio jest jej trudniej. Warto być teraz blisko.",
      },
    },
    helpLink: "Zobacz, gdzie szukać wsparcia",
    reminderTitle: "Na dziś",
    narrativeLabel: "Opis",
    sample: "Przykładowy tekst",
    generated: (when) => `Przygotowano ${when}`,
  },

  start: {
    greeting: (name) => `Cześć, ${name}`,
  },

  account: {
    loginTitle: "Zaloguj się",
    loginLead: "Dobrze, że jesteś. Zaloguj się, żeby zobaczyć swoją grupę.",
    registerTitle: "Załóż konto",
    registerLead: "To zajmie chwilę. Potem założysz grupę albo dołączysz do niej z zaproszenia.",
    email: "Adres e-mail",
    password: "Hasło",
    newPasswordHint: "Co najmniej 8 znaków.",
    name: "Jak mamy się do Ciebie zwracać?",
    nameHint: "Imię albo zdrobnienie. Zobaczą je osoby w Twojej grupie.",
    loginSubmit: "Zaloguj się",
    registerSubmit: "Załóż konto",
    toRegister: "Nie masz jeszcze konta?",
    toRegisterLink: "Załóż konto",
    toLogin: "Masz już konto?",
    toLoginLink: "Zaloguj się",
    errors: {
      emailMissing: "Wpisz adres e-mail.",
      passwordMissing: "Wpisz hasło.",
      passwordShort: "Hasło musi mieć co najmniej 8 znaków.",
      nameMissing: "Wpisz imię albo zdrobnienie.",
    },
  },
};
