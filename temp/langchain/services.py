import os
from pinecone import Pinecone, ServerlessSpec
from temp.openaiService import generate_summary
from user.models import UserSummary  # Django 모델 (MySQL 저장)


# Pinecone 인스턴스 생성
def get_pinecone_instance():
    return Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


# Pinecone 인덱스 생성 또는 가져오기
def get_pinecone_index(instance, index_name):
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


# Pinecone의 모든 데이터 가져오기
def get_all_data_from_pinecone(instance, index_name):
    """
    Pinecone에 저장된 모든 데이터의 메타데이터를 가져옵니다.
    """
    index = get_pinecone_index(instance, index_name)
    # Pinecone 인덱스에서 모든 데이터를 쿼리
    results = index.describe_index_stats()
    total_vectors = results['total_vector_count']

    if total_vectors == 0:
        return []

    # 모든 벡터의 메타데이터 가져오기
    data = []
    for vector_id, metadata in results['namespaces'].items():
        if "metadata" in metadata:
            data.append(metadata["metadata"]["original_text"])
    return data


# 텍스트를 엔터 기준으로 분할
def split_text_by_linebreaks(text):
    """
    텍스트를 엔터(\n) 기준으로 분할
    """
    return [chunk.strip() for chunk in text.split("\n") if chunk.strip()]


# 요약 생성
def summarize_text_with_gpt(text_chunk):
    """
    GPT를 사용하여 텍스트를 요약합니다.
    """
    return generate_summary(text_chunk)


# 결과 저장
def save_summary_to_mysql_and_pinecone(user_id, summaries):
    """
    요약 결과를 MySQL과 Pinecone에 저장
    """
    try:
        pinecone_instance = get_pinecone_instance()
        pinecone_index = get_pinecone_index(pinecone_instance, os.getenv("PINECONE_INDEX_NAME"))

        for summary in summaries:
            # MySQL 저장
            UserSummary.objects.create(
                user_id=user_id,
                topic=summary["topic"],
                summary=summary["summary_text"],
            )

            # Pinecone 저장
            pinecone_index.upsert(vectors=[
                {
                    "id": summary["topic"],  # 주제별 ID
                    "values": [0.1] * 1536,  # 예제 벡터 (실제 벡터 사용 필요)
                    "metadata": summary,
                }
            ])
    except Exception as e:
        raise RuntimeError(f"Error saving summary: {e}")
