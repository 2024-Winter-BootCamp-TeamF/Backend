from celery import shared_task
from .services import get_pinecone_instance, get_pinecone_index
import os
import redis
import json
from temp.openaiService import get_embedding


redis_client = redis.StrictRedis(host="redis", port=6379, db=0)


@shared_task
def upload_redis_to_pinecone(user_id):
    """
    Redis 데이터를 Pinecone으로 업로드하는 작업
    """
    try:
        # Redis 키 가져오기
        keys = redis_client.keys("pdf:*:page:*")
        if not keys:
            return {"status": "error", "message": "No data found in Redis."}

        # Pinecone 초기화
        instance = get_pinecone_instance()
        index_name = os.getenv("PINECONE_INDEX_NAME", "pdf-index")
        index = get_pinecone_index(instance, index_name)

        for key in sorted(keys):
            page_data = redis_client.get(key)
            if not page_data:
                continue

            # Redis에서 데이터 로드
            page_content = json.loads(page_data.decode("utf-8"))
            text_field = page_content.get("text")
            file_name = page_content.get("file_name", "unknown")  # 파일 이름 기본값 설정

            # 텍스트 처리
            if isinstance(text_field, dict) and "text" in text_field:
                text = text_field["text"]
            elif isinstance(text_field, str):
                text = text_field
            else:
                continue

            # 벡터 생성
            vector = get_embedding(text)

            # Pinecone에 업로드
            index.upsert([
                (
                    f"{key.decode('utf-8')}",  # Redis 키를 사용한 데이터 ID
                    vector,  # 생성된 벡터
                    {  # 메타데이터
                        "page_number": page_content.get("page_number"),
                        "file_name": file_name,
                        "original_text": text,
                        "category": determine_category(file_name),
                        "user_id": user_id,  # 사용자 ID 추가
                    }
                )
            ], namespace=str(user_id))

        # Redis 데이터 전체 삭제
        redis_client.flushdb()

        return {"status": "success", "message": "All data uploaded to Pinecone successfully"}

    except Exception as e:
        return {"status": "error", "message": f"Failed to upload to Pinecone: {str(e)}"}


def determine_category(file_name):
    """
    파일 이름을 기반으로 카테고리를 결정합니다.
    """
    lecture_keywords = ["족보", "수시", "중간", "기말", "고사", "quiz", "퀴즈"]
    file_name_lower = file_name.lower()  # 파일 이름 소문자로 변환

    if any(keyword in file_name_lower for keyword in lecture_keywords):
        return "genealogy"  # 족보

    return "lecture_notes"  # 기본값
