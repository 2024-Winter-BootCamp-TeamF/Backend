# Generated by Django 4.2.17 on 2025-01-07 06:58

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Item",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=100)),
                ("description", models.TextField()),
                ("created", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
