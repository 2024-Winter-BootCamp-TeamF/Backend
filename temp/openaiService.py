import openai
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OpenAI_API_Key")


def ask_openai(prompt: str, model: str = "gpt-4", max_tokens: int = 150, temperature: float = 0.7) -> dict:
    """
    OpenAI API와 통신하여 답변을 반환합니다.
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


def generate_summary(text: str) -> dict:
    """
    텍스트 요약을 생성합니다.
    """
    prompt = f"파일의 상태나 그림의 위치같은거 말고 1페이지 부터 순서대로 한국말로 강의자료의 내용을 초보자도 알기 쉽게 정리해줘 페이지 수도 언급하지마:\n\n{text}"
    return ask_openai(prompt, max_tokens=500)


def generate_problem(text: str) -> dict:
    """
    텍스트 기반 문제를 생성합니다.
    """
    prompt = f"해당 텍스트 기반으로 문제를 만들어줘:\n\n{text}"
    return ask_openai(prompt, max_tokens=500)
