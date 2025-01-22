from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .tasks import process_summary_task, delete_user_data_from_pinecone, generate_summary_and_pdf
from .utils import text_to_pdf
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, Http404
from temp.pinecone.models import PineconeSummary

class SummaryAPIView(APIView):
    """
    주제별 요약을 생성하고 PDF URL 반환
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Generate summaries for the given topics and return a PDF URL.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "topics": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="List of topics to generate summaries for (e.g., ['AI', 'Machine Learning']).",
                ),
                "top_k": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Number of top results to retrieve for each topic.",
                    default=10
                )
            },
            required=["topics"],
        ),
        responses={
            200: openapi.Response(
                description="Summary generated and PDF URL returned.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "status": openapi.Schema(type=openapi.TYPE_STRING),
                        "pdf_url": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="URL to the generated PDF file."
                        )
                    }
                ),
            ),
            400: openapi.Response(description="Bad Request. Missing or invalid input."),
        }
    )
    def post(self, request):
        user_id = request.user.id
        topics = request.data.get("topics")
        top_k = request.data.get("top_k", 10)

        if not topics or not isinstance(topics, list):
            return Response({"error": "Topics are required and must be a list."}, status=status.HTTP_400_BAD_REQUEST)

        result = generate_summary_and_pdf(user_id, topics, top_k)
        if result["status"] == "success":
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class DeleteUserDataView(APIView):
    """
    현재 사용자의 Pinecone 데이터를 삭제하는 API
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Delete all Pinecone data for the current user.",
        responses={
            202: "Data deletion task started successfully.",
            500: "Internal server error.",
        },
    )
    def delete(self, request):
        try:
            user_id = request.user.id  # 인증된 유저 ID 가져오기
            task = delete_user_data_from_pinecone.delay(user_id)  # Celery 비동기 작업 호출

            return Response(
                {
                    "message": "Data deletion task started successfully.",
                    "task_id": task.id,
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to start deletion task: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class PDFGenerateView(APIView):
    """
    MySQL에서 텍스트 데이터를 가져와 PDF로 변환해 반환
    """
    def get(self, request, redis_key):
        try:
            # MySQL에서 해당 redis_key와 관련된 데이터 가져오기
            summary_instance = PineconeSummary.objects.get(redis_key=redis_key)
            summary_text = summary_instance.summary_text  # 요약본 가져오기

            if not summary_text:
                raise Http404("Summary text not found.")

            # PDF 생성
            pdf_buffer = text_to_pdf(summary_text)

            # PDF 반환
            return FileResponse(pdf_buffer, as_attachment=True, filename=f"{redis_key}_summary.pdf")

        except PineconeSummary.DoesNotExist:
            return Response({"error": "Summary not found for the given redis_key."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
