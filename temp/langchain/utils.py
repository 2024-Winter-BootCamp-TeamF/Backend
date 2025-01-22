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

def text_to_pdf(text_data):
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
