from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        from .ai import get_provider
        from .ai.knowledge import get_knowledge

        # Fail at startup, not on the first request, when AI_PROVIDER or KNOWLEDGE_SOURCE is not
        # available or the curated file does not load.
        get_provider()
        get_knowledge()
