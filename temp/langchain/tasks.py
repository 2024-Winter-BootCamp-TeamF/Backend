import os

from celery import shared_task
from .services import (
    get_pinecone_instance,
    get_all_data_from_pinecone,
    split_text_by_linebreaks,
    summarize_text_with_gpt,
    save_summary_to_mysql_and_pinecone,
)


@shared_task
def process_summary_task(user_id):
    """
    Pinecone 데이터를 기반으로 요약 작업을 수행하는 Celery 태스크
    """
    try:
        # Pinecone 데이터 가져오기
        pinecone_instance = get_pinecone_instance()
        index_name = os.getenv("PINECONE_INDEX_NAME")
        all_data = get_all_data_from_pinecone(pinecone_instance, index_name)

        if not all_data:
            return {"status": "error", "message": "No data found in Pinecone"}

        # 텍스트를 엔터 기준으로 분할
        summaries = []
        for data in all_data:
            text_chunks = split_text_by_linebreaks(data)

            # 각 텍스트 블록을 GPT로 요약
            for text_chunk in text_chunks:
                summary_text = summarize_text_with_gpt(text_chunk)
                if summary_text:
                    summaries.append({"topic": "Generated Topic", "summary_text": summary_text})

        # 요약 결과 저장
        save_summary_to_mysql_and_pinecone(user_id, summaries)
        return {"status": "success", "message": "Summaries created and saved successfully"}

    except Exception as e:
        return {"status": "error", "message": str(e)}
