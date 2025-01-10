import openai
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OpenAI_API_Key")

# OpenAI 요청 처리 함수
def ask_openai(prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 150, temperature: float = 0.7) -> dict:
    """
    OpenAI API와 통신하여 답변을 반환합니다.
    :param prompt: 사용자 입력 문자열
    :param model: OpenAI 모델 이름 (기본값: gpt-3.5-turbo)
    :param max_tokens: 최대 토큰 수
    :param temperature: 응답의 다양성 (0.0 = 보수적, 1.0 = 창의적)
    :return: API 응답 데이터 딕셔너리
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return {
            "success": True,
            "response": response['choices'][0]['message']['content']
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
