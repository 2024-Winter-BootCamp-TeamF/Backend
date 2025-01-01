FROM python:3.12.4

# 작업 디렉토리를 설정
WORKDIR /app

# 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc && \
    apt-get clean

# 의존성 파일 복사 및 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . /app/

# 포트 노출
EXPOSE 8000

# 기본 명령어 실행 (Django 개발 서버 실행)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
