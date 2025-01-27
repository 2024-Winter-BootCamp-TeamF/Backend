import redis
import os
import json
from celery import shared_task
import pinecone
from django.conf import settings
from .service import get_pinecone_instance, get_pinecone_index
from temp.openaiService import get_embedding
from ..text.tasks import determine_category

redis_client = redis.StrictRedis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    db=0
)
@shared_task
def upload_file_id_to_pinecone_task(file_id, file_keys, user_id):
    """
    Celery 태스크: 특정 file_id에 해당하는 모든 데이터를 Pinecone에 업로드
    """
    try:
        # Pinecone 인스턴스 및 인덱스 가져오기
        instance = get_pinecone_instance()
        index_name = os.getenv("PINECONE_INDEX_NAME", "pdf-index")
        index = get_pinecone_index(instance, index_name)

        # Redis에서 데이터 처리
        for key in file_keys:
            page_data = redis_client.get(key)
            if not page_data:
                print(f"Redis data not found for key {key}")
                continue

            # Redis 데이터 로드
            page_content = json.loads(page_data.decode("utf-8"))
            text_field = page_content.get("text")
            file_name = page_content.get("file_name", "unknown")

            # 텍스트 처리
            if isinstance(text_field, dict) and "text" in text_field:
                text = text_field["text"]
            elif isinstance(text_field, str):
                text = text_field
            else:
                raise ValueError(f"Invalid 'text' format in Redis data for key {key}")

            # 텍스트를 벡터화
            vector = get_embedding(text)

            # Pinecone에 데이터 업로드
            index.upsert([
                (
                    f"{user_id}:{key}",  # Redis 키를 포함한 데이터 ID
                    vector,
                    {  # 메타데이터
                        "page_number": page_content.get("page_number"),
                        "file_name": file_name,
                        "original_text": text,
                        "category": determine_category(file_name),
                        "user_id": user_id,
                    }
                )
            ], namespace=str(user_id))

        # 처리 완료 후 Redis에서 모든 키 삭제
        redis_client.delete(*file_keys)

        return {"status": "success", "message": f"File ID {file_id} processed successfully"}

    except Exception as e:
        return {"status": "error", "message": f"Failed to process file_id {file_id}: {str(e)}"}
