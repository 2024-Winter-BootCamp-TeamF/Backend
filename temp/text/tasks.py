from .services import get_pinecone_instance, get_pinecone_index
from temp.openaiService import get_embedding
from celery import shared_task
import redis
import json
import os

redis_client = redis.StrictRedis(host="redis", port=6379, db=0)


@shared_task
def upload_to_pinecone_task(user_id):
    """
    Redis에서 데이터를 가져와 Pinecone에 업로드하는 비동기 작업
    """
    try:
        # Pinecone 인스턴스 및 인덱스 가져오기
        instance = get_pinecone_instance()
        index_name = os.getenv("PINECONE_INDEX_NAME", "pdf-index")
        index = get_pinecone_index(instance, index_name)

        # Redis에서 데이터 가져오기
        keys = redis_client.keys("pdf:*:page:*")
        if not keys:
            return {
                "status": "error",
                "message": "No data found in Redis."
            }

        for key in sorted(keys):
            page_data = redis_client.get(key)
            if not page_data:
                continue

            try:
                # Redis 데이터 파싱
                page_content = json.loads(page_data.decode("utf-8"))
                text_field = page_content.get("text")
                file_name = page_content.get("file_name", "unknown")
                page_number = page_content.get("page_number")

                # 텍스트 임베딩 생성
                vector = get_embedding(text_field)

                # Pinecone에 데이터 업로드
                index.upsert([
                    (
                        f"{key.decode('utf-8')}",  # Redis 키를 데이터 ID로 사용
                        vector,
                        {
                            "page_number": page_number,
                            "file_name": file_name,
                            "original_text": text_field,
                            "category": determine_category(file_name),
                            "user_id": user_id,  # 사용자 ID 추가
                        }
                    )
                ], namespace=str(user_id))

            except Exception as e:
                print(f"Failed to process key {key}: {e}")
                continue

        # Redis 데이터 삭제
        redis_client.flushdb()

        return {
            "status": "success",
            "message": "All data uploaded to Pinecone successfully."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to upload data to Pinecone: {e}"
        }


def determine_category(file_name):
    """
    파일 이름을 기반으로 카테고리 결정
    """
    lecture_keywords = ["족보", "수시", "중간", "기말", "고사", "quiz", "퀴즈"]
    file_name_lower = file_name.lower()

    if any(keyword in file_name_lower for keyword in lecture_keywords):
        return "genealogy"
    return "lecture_notes"
