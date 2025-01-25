import openai
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OpenAI_API_Key")

def get_embedding(text, model="text-embedding-ada-002"):
    """
    OpenAI 임베딩을 생성하는 함수
    """
    try:
        # text가 문자열인지 확인
        if not isinstance(text, str):
            raise ValueError(f"Expected 'text' to be a string, but got {type(text).__name__}")

        # 텍스트가 비어있거나 None인 경우 예외 처리
        if not text.strip():
            raise ValueError("Text for embedding cannot be empty or null.")

        # 텍스트 길이가 너무 긴 경우 자르기
        max_tokens = 8191  # text-embedding-ada-002 모델의 최대 토큰 수 제한
        if len(text) > max_tokens:
            text = text[:max_tokens]

        # OpenAI API 호출
        response = openai.Embedding.create(
            input=text,
            model=model
        )

        # 임베딩 벡터 반환
        return response["data"][0]["embedding"]

    except Exception as e:
        raise ValueError(f"Failed to generate embedding: {str(e)}")

def ask_openai(prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 150, temperature: float = 0.7) -> dict:
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
    if not text.strip():
        return {"success": False, "error": "Input text is empty or null."}

    prompt = (
        "다음 텍스트를 기반으로 주요 내용을 구조화하여 요약해 주세요. "
        "요약은 다음 형식을 따릅니다: "
        "1) 각 주요 아이디어를 별도의 항목으로 정리합니다. "
        "2) 항목당 1~2개의 간결한 문장을 사용하여 핵심 내용을 설명합니다. "
        "3) 텍스트의 전반적인 주제를 먼저 간단히 요약한 후 세부 내용을 항목화하세요. "
        "이 방식은 독자가 텍스트를 더 빠르고 쉽게 이해할 수 있도록 돕습니다. "
        "텍스트를 강조하기 위한 *을 절대 사용하지 마세요."
        "정리된 번호마다 \n로 간격을 띄우세요."
        f"텍스트: {text}"
    )

    return ask_openai(prompt, max_tokens=500)


def generate_problem(text: str) -> dict:
    """
    텍스트 기반 문제를 생성합니다.
    """
    prompt = f"해당 텍스트 기반으로 문제를 만들어줘:\n\n{text}"
    return ask_openai(prompt, max_tokens=500)
