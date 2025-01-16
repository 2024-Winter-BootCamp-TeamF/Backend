### service.py
import os
from pinecone import Pinecone, ServerlessSpec

# Pinecone 초기화
def get_pinecone_instance():
    """
    Pinecone 인스턴스를 생성
    """
    return Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


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


def query_pinecone_data(instance, index_name, redis_key):
    """
    Pinecone에서 특정 Redis 키와 연관된 데이터 조회
    """
    index = get_pinecone_index(instance, index_name)
    result = index.fetch(ids=[redis_key])
    if not result or redis_key not in result["vectors"]:
        return None
    return result["vectors"][redis_key]

def query_pinecone_original_text(instance, index_name, redis_key):
    """
    Pinecone에서 특정 Redis 키와 연관된 메타데이터 중 original_text를 조회
    """
    index = get_pinecone_index(instance, index_name)
    result = index.fetch(ids=[redis_key])
    if not result or redis_key not in result["vectors"]:
        return None
    metadata = result["vectors"][redis_key].get("metadata", {})
    return metadata.get("original_text")
