from django.db import models

# Create your models here.
class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('MCQ', '객관식'),
        ('SAQ', '주관식'),
    ]

    question_type = models.CharField(max_length=3, choices=QUESTION_TYPE_CHOICES)
    question_text = models.TextField()
    choices = models.JSONField(null=True, blank=True)  # 객관식 선택지 저장
    answer = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question {self.id}: {self.question_text}"


class UserAnswer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user_answer = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"UserAnswer for Question ID {self.question.id} - Correct: {self.is_correct}"
