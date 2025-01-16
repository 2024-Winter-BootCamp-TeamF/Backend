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
        "다음 텍스트는 대학 강의 자료입니다. "
        "당신은 세계에서 가장 뛰어난 대학 강의 학습 보조 도구입니다. "
        "주요 개념과 핵심 내용을 간단히 요약해 주세요.\n"
        "불필요한 세부사항, 예시, 또는 장황한 설명은 생략해 주세요.\n\n"
        f"텍스트: {text}"
    )

    return ask_openai(prompt, max_tokens=500)


def generate_problem(text: str) -> dict:
    """
    텍스트 기반 문제를 생성합니다.
    """
    prompt = f"해당 텍스트 기반으로 문제를 만들어줘:\n\n{text}"
    return ask_openai(prompt, max_tokens=500)
