from django.db import models

class UploadedPDF(models.Model):
    file = models.FileField(upload_to='pdfs/')  # Media 디렉토리에 파일 저장
    file_name = models.CharField(max_length=255)  # 사용자 친화적인 파일 이름 저장
    uploaded_at = models.DateTimeField(auto_now_add=True)  # 업로드 시간 기록

    def __str__(self):
        return self.file_name