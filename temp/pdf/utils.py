import fitz
import json

from pymupdf4llm.helpers.pymupdf_rag import to_markdown

from config.settings import redis_client

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

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


def extract_and_store_pdf_to_redis(pdf_path, file_id):
    """
    PDF 텍스트를 페이지별로 Redis에 저장
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

        # 총 페이지 수 반환
        return len(md_text)

    except Exception as e:
        print("Error in extract_and_store_pdf_to_redis:", str(e))  # 에러 출력
        raise e

def pdf_to_text(text_data):
    """
    주어진 텍스트 데이터를 PDF로 변환
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    # 텍스트 위치 및 줄 바꿈 처리
    y_position = 750
    line_height = 15
    for line in text_data.split('\n'):
        if y_position < 50:  # 페이지 끝이면 새 페이지 추가
            pdf.showPage()
            y_position = 750
        pdf.drawString(50, y_position, line)
        y_position -= line_height

    pdf.save()
    buffer.seek(0)
    return buffer
