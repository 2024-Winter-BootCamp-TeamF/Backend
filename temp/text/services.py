import os
from pinecone import Pinecone, ServerlessSpec


def get_pinecone_instance():
    """
    Pinecone 인스턴스를 생성
    """
    return Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


def get_pinecone_index(instance, index_name):
    """
    Pinecone 인덱스를 가져옵니다. 없으면 생성합니다.
    """
    if index_name not in [i.name for i in instance.list_indexes()]:
        spec = ServerlessSpec(
            cloud="aws",
            region=os.getenv("PINECONE_ENVIRONMENT"),
        )
        instance.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=spec,
        )
    return instance.Index(index_name)
