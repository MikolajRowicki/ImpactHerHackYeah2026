from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        from .ai import get_provider

        # Fail at startup, not on the first request, when AI_PROVIDER is not available.
        get_provider()
