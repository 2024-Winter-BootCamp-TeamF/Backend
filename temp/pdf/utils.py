import fitz
import json
import os
from fpdf import FPDF
from PIL import Image
from django.conf import settings
from pymupdf4llm.helpers.pymupdf_rag import to_markdown
from config.settings import redis_client
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import subprocess

# 한국어 폰트 등록 (나눔고딕 예시)
FONT_NAME = "NanumGothic"
FONT_PATH = settings.FONT_PATH  # settings.py에서 정의한 경로 사용
pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
PAGE_WIDTH, PAGE_HEIGHT = letter  # 페이지 크기 (폭, 높이)
LEFT_MARGIN = 50  # 왼쪽 여백
RIGHT_MARGIN = 50  # 오른쪽 여백
LINE_HEIGHT = 15  # 줄 간격


def convert_rect_objects(data):
    """데이터 구조에서 Rect 객체를 재귀적으로 변환"""
    if isinstance(data, dict):
        # 딕셔너리 내부 Rect 변환
        return {k: convert_rect_objects(v) for k, v in data.items()}
    elif isinstance(data, list):
        # 리스트 내부 Rect 변환
        return [convert_rect_objects(item) for item in data]
    elif isinstance(data, fitz.Rect):
        # Rect 객체를 [x0, y0, x1, y1] 리스트로 변환
        return [data.x0, data.y0, data.x1, data.y1]
    else:
        # Rect가 아닌 경우 그대로 반환
        return data


def extract_and_store_pdf_to_redis(pdf_path, file_id, file_name):
    """
    PDF 텍스트를 페이지별로 Redis에 저장하고 파일 이름 메타데이터 추가
    """
    try:
        # PDF 텍스트를 페이지별로 추출
        md_text = to_markdown(pdf_path, page_chunks=True)

        # 반환된 데이터 디버깅용 출력
        print("Original Extracted Data:", md_text)

        # Rect 객체를 재귀적으로 변환
        md_text = convert_rect_objects(md_text)

        # 변환된 데이터 디버깅용 출력
        print("Converted Data for Redis:", md_text)

        # Redis에 페이지별 데이터 저장
        for page_num, page_text in enumerate(md_text, start=1):
            redis_key = f"pdf:{file_id}:page:{page_num}"
            redis_client.set(redis_key, json.dumps({"page_number": page_num, "text": page_text}))

        # Redis에 파일 메타데이터 저장
        meta_key = f"pdf:{file_id}:meta"
        redis_client.set(meta_key, json.dumps({"file_name": file_name, "total_pages": len(md_text)}))

        # 총 페이지 수 반환
        return len(md_text)

    except Exception as e:
        print("Error in extract_and_store_pdf_to_redis:", str(e))
        raise e

def extract_and_store_text_to_redis(input_text, file_id, file_name):
    """
    텍스트를 줄바꿈 단위로 Redis에 저장하고 파일 이름 메타데이터 추가
    """
    try:
        # 텍스트를 줄바꿈 기준으로 나누기
        text_lines = input_text.splitlines()

        # 빈 줄 제거
        text_lines = [line.strip() for line in text_lines if line.strip()]

        # 변환된 데이터 디버깅용 출력
        print("Processed Text Data for Redis:", text_lines)

        # Redis에 줄 단위 데이터 저장
        for line_num, line_text in enumerate(text_lines, start=1):
            redis_key = f"text:{file_id}:line:{line_num}"
            redis_client.set(redis_key, json.dumps({"line_number": line_num, "text": line_text}))

        # Redis에 파일 메타데이터 저장
        meta_key = f"text:{file_id}:meta"
        redis_client.set(meta_key, json.dumps({"file_name": file_name, "total_lines": len(text_lines)}))

        # 총 줄 수 반환
        return len(text_lines)

    except Exception as e:
        print("Error in extract_and_store_text_to_redis:", str(e))
        raise e

def pdf_to_text(text_data):
    """
    주어진 텍스트 데이터를 한국어 폰트를 사용하여 PDF로 변환.
    왼쪽 및 오른쪽 여백을 설정하여 텍스트가 잘리지 않도록 처리.
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont(FONT_NAME, 12)  # 폰트 설정

    max_text_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN  # 텍스트가 출력될 최대 너비
    y_position = PAGE_HEIGHT - 50  # 상단 여백
    lines = text_data.split('\n')  # 입력 텍스트를 줄 단위로 분리

    for line in lines:
        # 한 줄이 너무 길면 줄바꿈 처리
        words = line.split(' ')
        current_line = ''
        for word in words:
            # 단어를 추가한 상태로 너비 측정
            test_line = f"{current_line} {word}".strip()
            text_width = pdf.stringWidth(test_line, FONT_NAME, 12)

            if text_width <= max_text_width:
                current_line = test_line
            else:
                # 현재 줄이 꽉 찼을 경우 출력하고 새로운 줄 시작
                pdf.drawString(LEFT_MARGIN, y_position, current_line)
                y_position -= LINE_HEIGHT

                # 페이지 하단에 도달하면 새로운 페이지 추가
                if y_position < 50:
                    pdf.showPage()
                    pdf.setFont(FONT_NAME, 12)
                    y_position = PAGE_HEIGHT - 50

                current_line = word

        # 남아있는 텍스트 출력
        if current_line:
            pdf.drawString(LEFT_MARGIN, y_position, current_line)
            y_position -= LINE_HEIGHT

            if y_position < 50:
                pdf.showPage()
                pdf.setFont(FONT_NAME, 12)
                y_position = PAGE_HEIGHT - 50

    pdf.save()
    buffer.seek(0)
    return buffer

def local_file_upload(file_path, uploaded_file):
    with open(file_path, 'wb') as temp_file:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)

def ppt_to_pdf(input_path, output_path):
    subprocess.run([
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        os.path.dirname(output_path),
        input_path
    ], check=True)

def word_to_pdf(input_path, output_path):
    # LibreOffice를 headless 모드로 실행하여 .docx 파일을 .pdf로 변환
    subprocess.run([
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        os.path.dirname(output_path),
        input_path
    ], check=True)

def image_to_pdf(input_path, output_path):
    image = Image.open(input_path)
    pdf = FPDF()
    pdf.add_page()

    image_width, image_height = image.size
    aspect_ratio = image_height / image_width
    pdf_width = 210  # A4 크기 (mm)
    pdf_height = pdf_width * aspect_ratio

    temp_image_path = "/tmp/temp_image.jpg"
    image.save(temp_image_path)

    pdf.image(temp_image_path, x=0, y=0, w=pdf_width, h=pdf_height)
    os.remove(temp_image_path)

    pdf.output(output_path)