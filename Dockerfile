# Python 3.12-slim 이미지 사용
FROM python:3.12-slim

# .pyc 파일 생성 억제
ENV PYTHONDONTWRITEBYTECODE=1

# 실시간 로그 출력을 위해 버퍼 최소화
ENV PYTHONUNBUFFERED=1

# 컨테이너 내부 디렉토리를 /backend로 설정
WORKDIR /backend

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    fonts-nanum \
    fonts-dejavu-core \
    fonts-liberation \
    gcc \
    libpq-dev \
    pkg-config \
    build-essential \
    default-libmysqlclient-dev \
    dos2unix \
    iputils-ping \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install --upgrade pip \
    && pip install poetry

# 프로젝트 의존성 파일 복사
COPY pyproject.toml poetry.lock ./

# DOS2UNIX로 줄바꿈 형식 변환
RUN dos2unix pyproject.toml poetry.lock

# Poetry로 의존성 설치 (dev 의존성 제외, 프로젝트 설치 생략)
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi --no-root

# 애플리케이션 소스코드 복사
COPY . .

# DOS2UNIX로 소스코드 줄바꿈 형식 변환
RUN find . -type f -exec dos2unix {} +

# Django 환경 변수 설정
ENV DJANGO_SETTINGS_MODULE=config.settings

# 포트 노출
EXPOSE 8000

# 폰트 복사
COPY media/fonts /app/media/fonts

# 기본 명령어 설정: Celery Worker 실행
CMD ["celery", "-A", "config", "worker", "--loglevel=info"]
