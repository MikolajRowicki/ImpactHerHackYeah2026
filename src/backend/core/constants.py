"""Closed sets shared by models, services and tests. They mirror contracts/openapi.yaml."""

ROLE_WOMAN = "woman"
ROLE_PARTNER = "partner"
ROLE_SUPPORTER = "supporter"
ROLES = (ROLE_WOMAN, ROLE_PARTNER, ROLE_SUPPORTER)

GROUP_PENDING = "pending"
GROUP_ACTIVE = "active"
GROUP_CLOSED = "closed"
GROUP_STATUSES = (GROUP_PENDING, GROUP_ACTIVE, GROUP_CLOSED)

MOODS = ("good", "okay", "low", "very_low")
SLEEPS = ("enough", "little", "almost_none")
ANXIETIES = ("none", "some", "strong")
ANSWER_VALUES = ("yes", "no", "unsure", "more_than_usual", "as_usual", "less_than_usual")

TASK_OPEN = "open"
TASK_CLAIMED = "claimed"
TASK_DONE = "done"
TASK_STATUSES = (TASK_OPEN, TASK_CLAIMED, TASK_DONE)

REMINDER_CHECK_IN = "check_in_due"
REMINDER_OBSERVATION = "observation_due"
REMINDER_TASK = "task_in_progress"
REMINDER_KINDS = (REMINDER_CHECK_IN, REMINDER_OBSERVATION, REMINDER_TASK)

VOIVODESHIPS = (
    "dolnoslaskie",
    "kujawsko_pomorskie",
    "lodzkie",
    "lubelskie",
    "lubuskie",
    "malopolskie",
    "mazowieckie",
    "opolskie",
    "podkarpackie",
    "podlaskie",
    "pomorskie",
    "slaskie",
    "swietokrzyskie",
    "warminsko_mazurskie",
    "wielkopolskie",
    "zachodniopomorskie",
)

INVITATION_DAYS = 7
