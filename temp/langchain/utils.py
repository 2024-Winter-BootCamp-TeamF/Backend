from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 한국어 폰트 등록
FONT_NAME = "NanumGothic"
FONT_PATH = settings.FONT_PATH  # settings.py에서 정의한 경로 사용
pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))

# PDF 페이지와 여백 설정
PAGE_WIDTH, PAGE_HEIGHT = letter  # 페이지 크기 (폭, 높이)
LEFT_MARGIN = 50  # 왼쪽 여백
RIGHT_MARGIN = 50  # 오른쪽 여백
TOP_MARGIN = 50  # 상단 여백
BOTTOM_MARGIN = 50  # 하단 여백
LINE_HEIGHT = 15  # 줄 간격

def text_to_pdf(topic_summaries):
    """
    여러 토픽과 요약을 PDF로 변환.
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont(FONT_NAME, 12)

    # 텍스트가 출력될 최대 너비 및 시작 위치
    max_text_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    y_position = PAGE_HEIGHT - TOP_MARGIN  # 상단 여백으로 시작

    for topic_summary in topic_summaries.split("\n\n"):
        # 단락별로 처리
        lines = topic_summary.split("\n")
        for line in lines:
            # 한 줄이 너무 길면 줄바꿈 처리
            words = line.split(' ')
            current_line = ''
            for word in words:
                test_line = f"{current_line} {word}".strip()
                text_width = pdf.stringWidth(test_line, FONT_NAME, 12)

                if text_width <= max_text_width:
                    current_line = test_line
                else:
                    # 현재 줄 출력
                    pdf.drawString(LEFT_MARGIN, y_position, current_line)
                    y_position -= LINE_HEIGHT

                    # 페이지 하단에 도달하면 새 페이지로 전환
                    if y_position < BOTTOM_MARGIN:
                        pdf.showPage()
                        pdf.setFont(FONT_NAME, 12)
                        y_position = PAGE_HEIGHT - TOP_MARGIN

                    current_line = word

            # 남아있는 텍스트 출력
            if current_line:
                pdf.drawString(LEFT_MARGIN, y_position, current_line)
                y_position -= LINE_HEIGHT

                # 페이지 하단에 도달하면 새 페이지로 전환
                if y_position < BOTTOM_MARGIN:
                    pdf.showPage()
                    pdf.setFont(FONT_NAME, 12)
                    y_position = PAGE_HEIGHT - TOP_MARGIN

        # 단락 간 간격 추가
        y_position -= LINE_HEIGHT

        # 페이지 하단에 도달하면 새 페이지로 전환
        if y_position < BOTTOM_MARGIN:
            pdf.showPage()
            pdf.setFont(FONT_NAME, 12)
            y_position = PAGE_HEIGHT - TOP_MARGIN

    pdf.save()
    buffer.seek(0)
    return buffer
