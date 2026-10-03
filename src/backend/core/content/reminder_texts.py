"""Polish texts of the reminders, general on purpose: no health data, no trend, no names."""

from ..constants import REMINDER_CHECK_IN, REMINDER_OBSERVATION, REMINDER_TASK

# Shown in the app.
IN_APP = {
    REMINDER_CHECK_IN: "Zajrzyj dziś do dziennika i zapisz, jak się czujesz.",
    REMINDER_OBSERVATION: "Poświęć chwilę i zapisz dzisiejszą obserwację.",
    REMINDER_TASK: "Masz zadanie w toku. Dokończ je albo oddaj komuś innemu.",
}

# Sent by e-mail: the subject and the line before the link.
EMAIL = {
    REMINDER_CHECK_IN: (
        "MaydayMama: dzisiejszy wpis w dzienniku",
        "Zajrzyj dziś do dziennika i zapisz, jak się czujesz. To zajmie chwilę.",
    ),
    REMINDER_OBSERVATION: (
        "MaydayMama: dzisiejsza obserwacja",
        "Poświęć chwilę i zapisz dzisiejszą obserwację. To pomaga całemu kręgowi bliskich.",
    ),
    REMINDER_TASK: (
        "MaydayMama: zadanie w toku",
        "Masz zadanie w toku. Dokończ je albo oddaj komuś innemu.",
    ),
}

EMAIL_GREETING = "Cześć,"
EMAIL_LINK_INTRO = "Otwórz aplikację:"
EMAIL_OFF_HINT = "Przypomnienia wyłączysz w ustawieniach aplikacji."
