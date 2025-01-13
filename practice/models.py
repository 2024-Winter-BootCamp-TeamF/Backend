from django.db import models


class Summary(models.Model):
    """
    요약 정보를 저장하는 모델
    """
    pdf_file_id = models.IntegerField()  # PDF 파일 ID
    summary_text = models.TextField()  # 요약된 텍스트
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시각

    def __str__(self):
        return f"Summary for PDF {self.pdf_file_id}"


class Problem(models.Model):
    """
    문제 정보를 저장하는 모델
    """
    pdf_file_id = models.IntegerField()  # PDF 파일 ID
    problem_text = models.TextField()  # 문제 텍스트
    problem_type = models.CharField(max_length=255)  # 문제 유형
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시각

    def __str__(self):
        return f"Problem for PDF {self.pdf_file_id}: {self.problem_type}"
