# Generated by Django 5.1.5 on 2025-01-16 13:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('temp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PineconeSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('redis_key', models.CharField(help_text='Redis에서 사용하는 고유 키', max_length=255, unique=True)),
                ('summary_text', models.TextField(help_text='생성된 요약본')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='요약 생성 시간')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='요약 업데이트 시간')),
            ],
        ),
    ]
