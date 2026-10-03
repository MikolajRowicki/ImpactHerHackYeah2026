"""Texts of the account e-mails. Each carries only the link, how long it works and a note to
ignore the message. No health data, no trend, no name of another person, nothing about a group.
"""

SIGNATURE = "Zespół MaydayMama"

IGNORE_NOTE = "Jeśli to nie Ty o to prosiłeś lub prosiłaś, po prostu zignoruj tę wiadomość."


def _body(*paragraphs: str) -> str:
    return "\n\n".join([*paragraphs, SIGNATURE]) + "\n"


def activation(link: str) -> tuple[str, str]:
    """The message that confirms an address. The link works for 3 days."""
    return (
        "Potwierdź swoje konto w MaydayMama",
        _body(
            "Cześć,",
            f"aby potwierdzić adres e-mail i włączyć konto, otwórz ten link:\n{link}",
            "Link działa 3 dni i można go użyć tylko raz.",
            IGNORE_NOTE,
        ),
    )


def password_reset(link: str) -> tuple[str, str]:
    """The message that lets a person choose a new password. The link works for 1 hour."""
    return (
        "Ustaw nowe hasło w MaydayMama",
        _body(
            "Cześć,",
            f"aby ustawić nowe hasło, otwórz ten link:\n{link}",
            "Link działa 1 godzina i można go użyć tylko raz.",
            IGNORE_NOTE,
        ),
    )


def account_exists(link: str) -> tuple[str, str]:
    """Sent when someone signs up with an address that already has an account."""
    return (
        "Masz już konto w MaydayMama",
        _body(
            "Cześć,",
            "ktoś próbował założyć konto na ten adres e-mail, ale to konto już istnieje. "
            "Możesz się po prostu zalogować.",
            f"Jeśli nie pamiętasz hasła, ustaw nowe tutaj:\n{link}",
            "Link działa 1 godzina i można go użyć tylko raz.",
            IGNORE_NOTE,
        ),
    )
