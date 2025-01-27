from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class MoreQuestion(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('MCQ', '객관식'),
        ('SAQ', '주관식'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Django 기본 User 모델과 연결
    question_type = models.CharField(max_length=3, choices=QUESTION_TYPE_CHOICES)
    question_topic = models.CharField(max_length=255)
    question_text = models.TextField()
    choices = models.JSONField(null=True, blank=True)  # 객관식 선택지 저장
    is_answer = models.BooleanField(default=False)
    answer = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"MoreQuestion {self.id}: {self.question_text}"

class MoreUserAnswer(models.Model):
    question = models.ForeignKey(MoreQuestion, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Django 기본 User 모델과 연결
    user_answer = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"UserAnswer for Question ID {self.question.id} - Correct: {self.is_correct}"