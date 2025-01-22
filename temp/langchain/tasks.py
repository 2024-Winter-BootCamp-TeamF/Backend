from .services import get_pinecone_instance, save_summaries_to_pdf, summarize_text_with_gpt
import os
from celery import shared_task
from temp.langchain.services import get_user_data_by_topic
from temp.openaiService import generate_summary
from user.models import UserSummary  # Django 모델 import


@shared_task
def process_summary_task(user_id, topic, top_k):
    """
    유저 ID와 주제를 기반으로 Pinecone에서 데이터를 검색하고 요약을 생성하는 Celery 작업
    """
    try:
        # Pinecone 인스턴스 및 인덱스 이름 가져오기
        instance = get_pinecone_instance()
        index_name = os.getenv("PINECONE_INDEX_NAME", "teamf")

        # 주제와 관련된 데이터 가져오기
        user_data = get_user_data_by_topic(instance, index_name, user_id, topic, top_k)

        # 데이터가 없을 경우 에러 반환
        if not user_data:
            return {
                "status": "error",
                "message": f"No data found for topic '{topic}' and user ID {user_id}."
            }

        # 원본 텍스트들을 합쳐 요약 생성
        combined_text = "\n".join([data["original_text"] for data in user_data])
        summary_result = generate_summary(combined_text)

        # 요약 생성 성공 여부 확인
        if summary_result["success"]:
            # MySQL에 요약 결과 저장
            UserSummary.objects.create(
                user_id=user_id,  # Django 모델의 ForeignKey
                topic=topic,  # 주제
                summary=summary_result["response"],  # 생성된 요약문
            )

            return {
                "status": "success",
                "message": "Summary created and saved successfully.",
                "summary": summary_result["response"],
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to generate summary: {summary_result['error']}",
            }

    except Exception as e:
        # 에러 발생 시 반환
        return {
            "status": "error",
            "message": f"Failed to process summary task: {str(e)}"
        }


@shared_task
def delete_user_data_from_pinecone(user_id):
    """
    Pinecone에서 특정 유저 ID에 해당하는 모든 데이터를 삭제하는 작업
    """
    try:
        # Pinecone 인스턴스 가져오기
        instance = get_pinecone_instance()
        index_name = os.getenv("PINECONE_INDEX_NAME", "pdf-index")
        index = instance.Index(index_name)

        # 해당 사용자 ID 네임스페이스에서 모든 데이터 삭제
        namespace = str(user_id)  # user_id를 namespace로 사용
        index.delete(delete_all=True, namespace=namespace)  # delete_all 플래그 설정

        return {
            "status": "success",
            "message": f"All data for user ID {user_id} has been deleted successfully."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to delete data for user ID {user_id}: {str(e)}"
        }

def generate_summary_and_pdf(user_id, topics, top_k):
    """
    여러 토픽에 대해 요약을 생성하고 PDF로 저장
    """
    try:
        instance = get_pinecone_instance()
        index_name = os.getenv("PINECONE_INDEX_NAME", "teamf")

        summaries = []
        for topic in topics:
            user_data = get_user_data_by_topic(instance, index_name, user_id, topic, top_k)
            if not user_data:
                continue

            combined_text = "\n".join([data["original_text"] for data in user_data])
            summary_result = summarize_text_with_gpt(combined_text)

            # JSON에서 "response" 키의 값만 사용
            if summary_result and summary_result.get("success"):
                summaries.append({
                    "topic": topic,
                    "summary_text": summary_result["response"]  # 요약된 텍스트만 저장
                })

        if summaries:
            pdf_url = save_summaries_to_pdf(user_id, summaries)
            return {"status": "success", "pdf_url": pdf_url}

        return {"status": "error", "message": "No summaries generated."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
