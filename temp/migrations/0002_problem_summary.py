# Generated by Django 5.1.4 on 2025-01-11 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('temp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pdf_file_id', models.IntegerField()),
                ('problem_text', models.TextField()),
                ('problem_type', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Summary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pdf_file_id', models.IntegerField()),
                ('summary_text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]