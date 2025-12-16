from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("registrar", "0006_remove_studentprofile_college_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="department",
            name="numeric_code",
            field=models.PositiveSmallIntegerField(
                "院系编号", unique=True, null=True, blank=True
            ),
        ),
    ]
