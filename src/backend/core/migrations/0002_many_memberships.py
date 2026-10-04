import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models



def refuse_if_shared(apps, schema_editor):
    """Going back to one membership per person is only possible while that is true."""
    Membership = apps.get_model("core", "Membership")
    many = (
        Membership.objects.values("user_id")
        .annotate(n=models.Count("id"))
        .filter(n__gt=1)
        .exists()
    )
    if many:
        raise RuntimeError(
            "Cannot go back: a person belongs to more than one group. "
            "Remove the extra memberships first."
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="membership",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="memberships",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name="membership",
            constraint=models.UniqueConstraint(
                fields=("user", "group"), name="membership_user_group_unique"
            ),
        ),
        migrations.AddConstraint(
            model_name="membership",
            constraint=models.UniqueConstraint(
                condition=models.Q(("role", "woman")),
                fields=("user",),
                name="membership_one_woman_per_user",
            ),
        ),
        # Last, so that going back runs it first, before any constraint is touched.
        migrations.RunPython(migrations.RunPython.noop, refuse_if_shared),
    ]
