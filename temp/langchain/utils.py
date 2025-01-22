from django.conf import settings


from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 한국어 폰트 등록 (나눔고딕 예시)
FONT_NAME = "NanumGothic"
FONT_PATH = settings.FONT_PATH  # settings.py에서 정의한 경로 사용
pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
PAGE_WIDTH, PAGE_HEIGHT = letter  # 페이지 크기 (폭, 높이)
LEFT_MARGIN = 50  # 왼쪽 여백
RIGHT_MARGIN = 50  # 오른쪽 여백
LINE_HEIGHT = 15  # 줄 간격

def text_to_pdf(topic_summaries):
    """
    여러 토픽과 요약을 PDF로 변환.
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont(FONT_NAME, 12)

    y_position = PAGE_HEIGHT - 50
    for topic_summary in topic_summaries.split("\n\n"):
        if y_position < 50:
            pdf.showPage()
            pdf.setFont(FONT_NAME, 12)
            y_position = PAGE_HEIGHT - 50

        pdf.drawString(LEFT_MARGIN, y_position, topic_summary)
        y_position -= LINE_HEIGHT * 2

    pdf.save()
    buffer.seek(0)
    return buffer
