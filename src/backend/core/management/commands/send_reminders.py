from django.core.management.base import BaseCommand

from core.services import reminders


class Command(BaseCommand):
    help = "E-mail the reminders that are due today, once per person and kind."

    def handle(self, *args, **options):
        counts = reminders.send_due_emails()
        # Counts only: never an address.
        self.stdout.write(
            f"send_reminders: sent={counts['sent']} already_sent={counts['already']} "
            f"refused={counts['refused']}"
        )
