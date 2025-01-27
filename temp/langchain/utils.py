import os

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
        for i, line in enumerate(lines):
            if i == 0 and line.lower().startswith("topic:"):  # 'topic:'으로 시작하는 첫 줄 처리
                pdf.setFont(FONT_NAME, 15)  # 'topic:' 크기 15로 설정
                pdf.drawString(LEFT_MARGIN, y_position, line)  # 'topic:' 출력
                y_position -= LINE_HEIGHT  # 줄 간격 조정
                pdf.setFont(FONT_NAME, 12)  # 다시 기본 크기 12로 설정
            else:
                # 나머지 줄 처리
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

def generate_pdf_from_summaries(user_id, summaries):
    """
    여러 토픽과 요약 데이터를 기반으로 PDF 파일을 생성.
    Args:
        user_id: 사용자 ID (파일 저장 경로를 구분하기 위해 사용)
        summaries: 각 토픽에 대한 요약 리스트 [{"topic": "Topic 1", "summary_text": "Summary 1"}, ...]
    Returns:
        PDF 파일 경로
    """
    # PDF 파일 저장 경로
    output_dir = os.path.join("media", "summaries", str(user_id))
    os.makedirs(output_dir, exist_ok=True)  # 디렉토리 없으면 생성
    pdf_file_path = os.path.join(output_dir, "summary.pdf")

    # PDF 생성
    pdf = canvas.Canvas(pdf_file_path, pagesize=letter)
    pdf.setFont(FONT_NAME, 12)

    # 텍스트 출력 위치 초기화
    max_text_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    y_position = PAGE_HEIGHT - TOP_MARGIN  # 상단 여백에서 시작

    for summary in summaries:
        # 토픽 출력 (크기 15, bold 스타일)
        pdf.setFont(FONT_NAME, 15)
        pdf.drawString(LEFT_MARGIN, y_position, f"Topic: {summary['topic']}")
        y_position -= LINE_HEIGHT

        # 페이지 하단에 도달하면 새 페이지로 전환
        if y_position < BOTTOM_MARGIN:
            pdf.showPage()
            pdf.setFont(FONT_NAME, 15)
            y_position = PAGE_HEIGHT - TOP_MARGIN

        # 요약 텍스트 출력 (크기 12)
        pdf.setFont(FONT_NAME, 12)
        lines = summary["summary_text"].split("\n")
        for line in lines:
            words = line.split(' ')
            current_line = ''

            for word in words:
                # 현재 줄에 단어 추가해도 폭을 초과하지 않는지 테스트
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

    # PDF 저장
    pdf.save()

    # 반환: 생성된 PDF 파일 경로
    return pdf_file_path