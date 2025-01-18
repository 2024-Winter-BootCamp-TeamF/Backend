from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class UserSummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Django 기본 User 모델과 연결
    topic = models.CharField(max_length=255)  # 요약 주제
    summary = models.TextField()  # 요약 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시간

    def __str__(self):
        return f"{self.user.username} - {self.topic}"
