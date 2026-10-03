from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .base import Generation, Provider, ProviderError
from .groq import GroqProvider
from .mock import MockProvider

PROVIDERS: dict[str, type[Provider]] = {"mock": MockProvider, "groq": GroqProvider}

__all__ = ["PROVIDERS", "Generation", "Provider", "ProviderError", "get_provider"]


def get_provider() -> Provider:
    """The provider chosen by AI_PROVIDER. Raises when the value is not available."""
    name = settings.AI_PROVIDER
    if name not in PROVIDERS:
        available = ", ".join(sorted(PROVIDERS))
        raise ImproperlyConfigured(
            f"AI_PROVIDER={name!r} is not available. Available values: {available}."
        )
    if name == "groq" and not settings.GROQ_API_KEY:
        raise ImproperlyConfigured(
            "AI_PROVIDER=groq needs GROQ_API_KEY. Set it in the environment."
        )
    return PROVIDERS[name]()
