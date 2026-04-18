from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("guests", "0002_remove_guest_event_remove_guest_organization_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="invite",
            name="couple_id",
            field=models.CharField(blank=True, db_index=True, max_length=36, null=True),
        ),
    ]

