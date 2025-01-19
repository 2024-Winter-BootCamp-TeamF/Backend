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
