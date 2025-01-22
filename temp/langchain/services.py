import os
from django.conf import settings
from pinecone import Pinecone, ServerlessSpec
from temp.openaiService import generate_summary, get_embedding
from user.models import UserSummary  # Django 모델 (MySQL 저장)
from io import BytesIO
from .utils import text_to_pdf
from .models import SummaryPDF

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


# 특정 사용자(user_id)의 모든 데이터를 Pinecone에서 가져오기
def get_user_data_by_topic(instance, index_name, user_id, topic, top_k):
    """
    Pinecone에서 특정 사용자가 올린 데이터 중 주제와 관련된 데이터를 가져옵니다.
    """
    try:
        index = get_pinecone_index(instance, index_name)

        # topic에 대한 임베딩 벡터 생성
        topic_embedding = get_embedding(topic)

        # Pinecone 쿼리를 통해 데이터 검색
        response = index.query(
            vector=topic_embedding,
            namespace=str(user_id),  # 유저 ID로 네임스페이스 필터링
            top_k=top_k,  # 최대 top_k개의 결과 반환
            include_metadata=True,  # 메타데이터 포함
        )

        # 검색 결과 데이터 추출
        if not response or "matches" not in response or len(response["matches"]) == 0:
            return None  # 데이터가 없으면 None 반환

        # 메타데이터에서 텍스트 추출
        return [
            {
                "original_text": match["metadata"].get("original_text", ""),
                "file_name": match["metadata"].get("file_name", "unknown"),
                "page_number": match["metadata"].get("page_number", 0),
            }
            for match in response["matches"]
            if "metadata" in match and "original_text" in match["metadata"]
        ]

    except Exception as e:
        raise RuntimeError(f"Error querying user data by topic from Pinecone: {e}")

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
                    "id": f"{user_id}:{summary['topic']}",  # 사용자 ID와 토픽 기반 ID
                    "values": [0.1] * 1536,  # 예제 벡터 (실제 벡터 사용 필요)
                    "metadata": summary,
                }
            ])

    except Exception as e:
        raise RuntimeError(f"Error saving summary: {e}")

def save_summaries_to_pdf(user_id, summaries):
    """
    요약 결과를 PDF로 변환하여 저장하고 URL 반환
    """
    try:
        pdf_buffer = BytesIO()
        topic_summaries = "\n\n".join(
            [f"Topic: {summary['topic']}\n\n{summary['summary_text']}" for summary in summaries]
        )
        pdf_buffer = text_to_pdf(topic_summaries)

        # 파일 저장 경로 설정
        file_name = f"summaries_{user_id}.pdf"
        file_path = os.path.join(settings.MEDIA_ROOT, "pdfs", file_name)

        with open(file_path, "wb") as pdf_file:
            pdf_file.write(pdf_buffer.getbuffer())

        # SummaryPDF 모델에 저장
        SummaryPDF.objects.create(
            user_id=user_id,
            file_name=file_name,
            file=f"pdfs/{file_name}",
        )

        # 반환할 URL 생성
        return f"{settings.MEDIA_URL}pdfs/{file_name}"
    except Exception as e:
        raise RuntimeError(f"Error saving summaries to PDF: {e}")
