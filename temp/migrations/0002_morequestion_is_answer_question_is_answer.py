# Generated by Django 5.1.5 on 2025-01-27 05:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('temp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='morequestion',
            name='is_answer',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='question',
            name='is_answer',
            field=models.BooleanField(default=False),
        ),
    ]
