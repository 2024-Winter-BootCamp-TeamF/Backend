import openai
import os
from dotenv import load_dotenv
import logging

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

def ask_openai(prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 2048, temperature: float = 0.7) -> dict:
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
            max_tokens=max_tokens,  # 요청 시 최대 토큰 동적으로 설정
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
logger = logging.getLogger(__name__)

def ask_openai_with_continue(prompt: str, model: str = "gpt-4", max_tokens: int = 2048, temperature: float = 0.7) -> dict:
    """
    OpenAI API와 통신하여 끊긴 응답을 처리하고 이어받습니다.
    """
    try:
        response_text = ""
        while True:
            # OpenAI API 호출
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # 응답에서 텍스트 추출
            response_part = response['choices'][0]['message']['content']
            response_text += response_part

            # 디버깅 로그: 현재까지 생성된 텍스트 출력
            print(f"[DEBUG] Current response part:\n{response_part}\n")
            logger.debug(f"Current response part: {response_part}")

            # 응답이 완결되었는지 확인
            if response_part.strip().endswith(".") or len(response_part) < max_tokens:
                # 응답이 끝났거나 토큰 제한에 도달하지 않은 경우 종료
                print("[DEBUG] Response is complete.")
                logger.debug("Response is complete.")
                break
            else:
                # 응답이 끊긴 경우 이어서 생성
                prompt = "Continue."  # 모델에 이어서 응답 요청
                print("[DEBUG] Sending 'Continue' prompt to OpenAI.")
                logger.debug("Sending 'Continue' prompt to OpenAI.")

        return {
            "success": True,
            "response": response_text.strip()
        }
    except Exception as e:
        # 예외 발생 시 로그 출력
        print(f"[ERROR] {str(e)}")
        logger.error(f"Error in ask_openai_with_continue: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def split_text(text: str, max_tokens: int = 3000) -> list:
    """
    긴 텍스트를 지정된 토큰 수 이하로 분할합니다.
    Args:
        text (str): 입력 텍스트
        max_tokens (int): 분할할 텍스트의 최대 토큰 수
    Returns:
        list: 분할된 텍스트 조각 리스트
    """
    sentences = text.split("\n")  # 문단 단위로 나눔
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # 현재 청크에 문장을 추가해도 max_tokens를 초과하지 않으면 추가
        if len(current_chunk) + len(sentence) <= max_tokens:
            current_chunk += sentence + "\n"
        else:
            # 현재 청크를 저장하고 새 청크 생성
            chunks.append(current_chunk.strip())
            current_chunk = sentence + "\n"

    # 마지막 청크 추가
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def preprocess_text(text: str) -> str:
    """
    텍스트를 전처리하여 불필요한 공백이나 특수 문자를 제거합니다.
    """
    text = text.replace("\n", " ").strip()  # 공백 및 줄바꿈 제거
    text = " ".join(text.split())  # 여러 공백을 하나로 축소
    return text


def generate_summary(text: str) -> dict:
    """
    긴 텍스트를 분할하여 요약을 생성하고, 끊긴 응답을 처리합니다.
    """
    if not text.strip():
        return {"success": False, "error": "Input text is empty or null."}

    # 텍스트 전처리
    text = preprocess_text(text)

    # 텍스트 분할
    text_chunks = split_text(text, max_tokens=1500)
    summaries = []

    for chunk in text_chunks:
        prompt = (
            "다음 텍스트를 기반으로 주요 내용을 구조화하여 요약해 주세요. "
            "요약 형식: "
            "1) 각 주요 아이디어를 별도의 항목으로 정리합니다. "
            "2) 항목당 1~2개의 간결한 문장을 사용하여 핵심 내용을 설명합니다. "
            "3) 텍스트의 전반적인 주제를 먼저 간단히 요약한 후 세부 내용을 항목화하세요. "
            "텍스트를 강조하기 위한 * 사용 금지"
            "정리된 번호마다 /n로 간격 띄우기"
            f"텍스트: {chunk}"
        )
        result = ask_openai_with_continue(prompt, max_tokens=1024)
        if result.get("success"):
            summaries.append(result["response"])
        else:
            summaries.append(f"Error processing chunk: {result.get('error')}")

    final_summary = "\n\n".join(summaries)
    return {"success": True, "response": final_summary}


def generate_problem(text: str) -> dict:
    """
    텍스트 기반 문제를 생성합니다.
    """
    prompt = f"해당 텍스트 기반으로 문제를 만들어줘:\n\n{text}"
    return ask_openai(prompt, max_tokens=500)
