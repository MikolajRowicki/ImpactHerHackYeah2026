from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .base import Generation, Provider
from .mock import MockProvider

# The Groq adapter arrives in a later change; until then "groq" is not available.
PROVIDERS: dict[str, type[Provider]] = {"mock": MockProvider}

__all__ = ["PROVIDERS", "Generation", "Provider", "get_provider"]


def get_provider() -> Provider:
    """The provider chosen by AI_PROVIDER. Raises when the value is not available."""
    name = settings.AI_PROVIDER
    try:
        return PROVIDERS[name]()
    except KeyError:
        available = ", ".join(sorted(PROVIDERS))
        raise ImproperlyConfigured(
            f"AI_PROVIDER={name!r} is not available. Available values: {available}."
        ) from None
