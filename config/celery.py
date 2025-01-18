import os
from celery import Celery

# Django 설정 모듈 환경 변수 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Celery 애플리케이션 생성
app = Celery('config')

# Celery 설정을 Django의 settings.py에서 가져옴
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django의 모든 앱에서 Task를 자동으로 등록
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
