# Generated by Django 5.1.3 on 2024-11-18 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("video_collection", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="video",
            name="video_id",
            field=models.CharField(default="bla", max_length=40, unique=True),
            preserve_default=False,
        ),
    ]