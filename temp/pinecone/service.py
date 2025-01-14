import os
import json
from pinecone import Pinecone, ServerlessSpec
from temp.openaiService import get_embedding


# Pinecone 초기화
def get_pinecone_instance():
    """
    Pinecone 인스턴스를 생성
    """
    return Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    # return Pinecone(api_key=api_key)


def get_pinecone_index(instance, index_name):
    """
    Pinecone 인덱스를 가져옵니다. 인덱스가 없으면 생성합니다.
    """
    # 인덱스가 없으면 생성
    if index_name not in [i.name for i in instance.list_indexes()]:
        # ServerlessSpec 정의
        spec = ServerlessSpec(
            cloud="aws",  # 클라우드 제공자
            region=os.getenv("PINECONE_ENVIRONMENT"),  # 리전 (환경 변수)
        )
        instance.create_index(
            name=index_name,
            dimension=1536,  # text-embedding-ada-002의 차원 수
            metric="cosine",  # 코사인 거리 측정
            spec=spec,
        )

    # 기존 인덱스를 가져옴
    return instance.Index(index_name)

def store_in_pinecone(instance, index_name, redis_client):
    """
    Redis에서 데이터를 가져와 Pinecone에 저장
    """
    try:
        keys = redis_client.keys("pdf:*:page:*")
        if not keys:
            return {"error": "No data found in Redis."}

        for key in keys:
            page_data = redis_client.get(key)
            if not page_data:
                continue

            # Redis 데이터 디코딩 및 JSON 로드
            page_content = json.loads(page_data.decode('utf-8'))

            # 'text' 필드 확인
            text = page_content.get("text", "")
            if not isinstance(text, str):
                raise ValueError(f"Invalid 'text' format in Redis data for key {key.decode('utf-8')}")

            # OpenAI 임베딩 생성
            vector = get_embedding(text)

            # Pinecone에 업로드
            metadata = {
                "redis_key": key.decode('utf-8'),
                "file_id": page_content.get("file_id", "unknown"),
                "page_number": page_content.get("page_number", "unknown"),
            }
            instance.index(index_name).upsert([
                {
                    "id": metadata["redis_key"],
                    "values": vector,
                    "metadata": metadata
                }
            ])

        return {"message": "All data uploaded to Pinecone successfully"}

    except Exception as e:
        return {"error": f"Failed to upload to Pinecone: {str(e)}"}