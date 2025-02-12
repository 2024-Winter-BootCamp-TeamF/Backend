import os
from pinecone import Pinecone, ServerlessSpec
from temp.openaiService import generate_summary
from .models import PineconeSummary

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


def query_pinecone_data(instance, index_name, redis_key, user_id):
    """
    Pinecone에서 특정 Redis 키와 연관된 데이터를 조회 (user_id 기반)
    """
    index = get_pinecone_index(instance, index_name)
    record_id = f"{user_id}:{redis_key}"  # user_id를 포함한 Redis 키를 사용
    result = index.fetch(ids=[record_id])
    if not result or record_id not in result["vectors"]:
        return None
    return result["vectors"][record_id]


def query_pinecone_original_text(instance, index_name, redis_key, user_id):
    """
    Pinecone에서 특정 Redis 키와 연관된 메타데이터 중 original_text를 조회 (user_id 기반)
    """
    index = get_pinecone_index(instance, index_name)
    record_id = f"{user_id}:{redis_key}"  # user_id를 포함한 Redis 키를 사용
    result = index.fetch(ids=[record_id])
    if not result or record_id not in result["vectors"]:
        return None
    metadata = result["vectors"][record_id].get("metadata", {})
    return metadata.get("original_text")


def process_and_save_summary(redis_key, original_text, user_id):
    """
    텍스트 요약을 생성하고 MySQL에 저장
    """
    summary_result = generate_summary(original_text)
    if summary_result["success"]:
        PineconeSummary.objects.create(
            redis_key=redis_key,
            user_id=user_id,  # 사용자 ID를 저장
            summary_text=summary_result["response"]
        )
        return summary_result["response"]
    else:
        raise ValueError(f"Failed to generate summary: {summary_result['error']}")
