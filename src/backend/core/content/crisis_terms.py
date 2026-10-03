"""Polish phrases that signal a crisis in the text of "say it for me".

A human who knows the topic must review this list before it goes to real users. It is a safety
net with fixed rules, not a classifier: a false alarm only shows the help block, a miss is worse,
so the list errs on the side of matching.

Every entry is already folded: lowercase, without Polish diacritics, words separated by one
space. `fold` turns a text into the same form. A phrase matches from the start of a word; it
may end inside a word, so a stem like "samobojst" covers every form.
"""

import re
import unicodedata

PHRASES = (
    # Not wanting to live, wanting to die.
    "nie chce zyc",
    "nie chce juz zyc",
    "nie chcialabym zyc",
    "nie chcialam zyc",
    "nie warto zyc",
    "nie ma sensu zyc",
    "nie widze sensu zycia",
    "zycie nie ma sensu",
    "wolalabym nie zyc",
    "wolalabym umrzec",
    "chce umrzec",
    "chcialabym umrzec",
    "chcialam umrzec",
    "chce zniknac",
    "chcialabym zniknac",
    "nie chce byc na tym swiecie",
    "bez mnie byloby lepiej",
    "wszystkim byloby lepiej beze mnie",
    "wszyscy byliby szczesliwsi beze mnie",
    # Suicide.
    "samobojst",
    "samobojcz",
    "zabic sie",
    "zabije sie",
    "zabiore sie",
    "sie zabic",
    "sie zabije",
    "sie zabiore",
    "odebrac sobie zycie",
    "odbiore sobie zycie",
    "sobie odebrac zycie",
    "sobie odbiore zycie",
    "odebralam sobie zycie",
    "targnac sie na zycie",
    "skonczyc ze soba",
    "skoncze ze soba",
    "skonczyc z zyciem",
    "skoncze z zyciem",
    "powiesic sie",
    "powiesze sie",
    "skoczyc z okna",
    "skoczyc z mostu",
    "wziac wszystkie tabletki",
    # Self-harm.
    "skrzywdzic sie",
    "sie skrzywdzic",
    "sie skrzywdze",
    "sobie krzywde zrobic",
    "sie powiesic",
    "sie powiesze",
    "sie okaleczac",
    "sie okaleczyc",
    "sie pociac",
    "skrzywdze sie",
    "zrobic sobie krzywde",
    "zrobie sobie krzywde",
    "samookalecz",
    "okaleczac sie",
    "okaleczyc sie",
    "pociac sie",
    "ciac sie",
    # Hurting the baby or the child.
    "zrobic krzywde dziecku",
    "zrobie krzywde dziecku",
    "zrobic krzywde dziecka",
    "zrobic krzywde malemu",
    "zrobic krzywde malej",
    "skrzywdzic dziecko",
    "skrzywdze dziecko",
    "skrzywdzic malego",
    "skrzywdzic mala",
    "skrzywdze malego",
    "skrzywdze mala",
    "zabic dziecko",
    "zabije dziecko",
    "zabic niemowle",
    "zrobic cos dziecku",
    "zrobie cos dziecku",
    "utopic dziecko",
    "udusic dziecko",
    "potrzasnac dzieckiem",
    "rzucic dzieckiem",
    # Added after review: forms that a new mother in distress commonly writes.
    "dluzej zyc",
    "nie mam po co zyc",
    "nie mam sily zyc",
    "dosc zycia",
    "dosc mi zycia",
    "mysle o smierci",
    "sie nie obudzic",
    "nie obudzic sie",
    "lepiej beze mnie",
    "beze mnie lepiej",
    "zabiciu sie",
    "z balkonu",
    "wyskoczyc",
    "zeby mnie nie bylo",
    "gdyby mnie nie bylo",
    "wyrzucic dziecko",
)

_NOT_A_LETTER = re.compile(r"[^a-z0-9]+")


def fold(text: str) -> str:
    """Lowercase, without diacritics, punctuation turned into single spaces."""
    # NFKD does not take apart the stroked l, so it is mapped by hand.
    lowered = text.lower().replace("ł", "l")
    decomposed = unicodedata.normalize("NFKD", lowered)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return _NOT_A_LETTER.sub(" ", stripped).strip()


def matches(text: str) -> bool:
    """True when the text holds a phrase of the list."""
    padded = f" {fold(text)}"
    return any(f" {phrase}" in padded for phrase in PHRASES)
