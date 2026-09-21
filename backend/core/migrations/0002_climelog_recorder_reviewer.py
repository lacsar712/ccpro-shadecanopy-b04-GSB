# 气候日志双签：记录人 / 复核人

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="climatelog",
            name="recorder",
            field=models.CharField(blank=True, default="", max_length=40),
        ),
        migrations.AddField(
            model_name="climatelog",
            name="reviewer",
            field=models.CharField(blank=True, default="", max_length=40),
        ),
    ]
