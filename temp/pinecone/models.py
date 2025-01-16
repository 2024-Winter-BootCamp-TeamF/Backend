from django.db import models


class PineconeSummary(models.Model):
    """
    Summary 모델: 원본 텍스트에서 생성된 요약본을 저장
    """
    redis_key = models.CharField(max_length=255, unique=True, help_text="Redis에서 사용하는 고유 키")
    summary_text = models.TextField(help_text="생성된 요약본")
    created_at = models.DateTimeField(auto_now_add=True, help_text="요약 생성 시간")
    updated_at = models.DateTimeField(auto_now=True, help_text="요약 업데이트 시간")

    def __str__(self):
        return f"Summary for {self.redis_key}"
