from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from user.models import UserSummary
from .tasks import process_summary_task, delete_user_data_from_pinecone
from rest_framework.permissions import IsAuthenticated


class SummaryAPIView(APIView):
    """
    Pinecone 데이터를 기반으로 주제별 요약을 생성하는 API
    """
    permission_classes = [IsAuthenticated]  # 로그인된 사용자만 접근 가능

    @swagger_auto_schema(
        operation_description="Generate summaries for multiple topics in Pinecone",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "top_k": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Number of top results to retrieve for each topic.",
                    default=10  # 기본값을 10으로 설정
                ),
                "topics": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="List of topics to summarize (e.g., ['machine learning', 'data science']).",
                )
            },
            required=["topics"],
        ),
        responses={
            202: openapi.Response(
                description="Summary generation tasks started successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "task_ids": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(type=openapi.TYPE_STRING),
                        ),
                    }
                ),
            ),
            400: openapi.Response(description="Topics are required."),
            500: openapi.Response(description="Internal server error."),
        },
    )
    def post(self, request):
        # 현재 사용자 ID 가져오기
        user_id = request.user.id

        # 요청 본문에서 topics 가져오기
        topics = request.data.get("topics")
        if not topics or not isinstance(topics, list):
            return Response({
                "error": "Topics are required and must be a list."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 요청 본문에서 top_k값 가져오기
        top_k = request.data.get("top_k")

        # 비동기 Celery 작업 호출 (각 topic에 대해 개별 작업 실행)
        task_ids = []
        for topic in topics:
            task = process_summary_task.delay(user_id, topic, top_k)
            task_ids.append(task.id)

        return Response({
            "message": "Summary generation tasks started successfully.",
            "task_ids": task_ids,  # 각 작업의 ID 반환
            "top_k": top_k, # top_k값
        }, status=status.HTTP_202_ACCEPTED)


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

class DeleteSummaryView(APIView):
    """
    특정 사용자가 자신의 요약 데이터를 삭제하는 API
    """

    @swagger_auto_schema(
        operation_description="Delete a summary by ID if the user is authorized",
        responses={
            200: openapi.Response(description="Summary deleted successfully"),
            404: openapi.Response(description="Summary not found or not authorized to delete"),
        }
    )
    def delete(self, request, summary_id):
        # 현재 요청을 보낸 사용자
        user = request.user

        try:
            # summary_id와 user를 기준으로 요약 데이터 검색
            summary = UserSummary.objects.get(id=summary_id, user=user)

            # 요약 데이터 삭제
            summary.delete()

            return Response({"message": "Summary deleted successfully"}, status=status.HTTP_200_OK)

        except UserSummary.DoesNotExist:
            # 사용자가 본인의 요약 데이터만 삭제할 수 있음
            return Response({"error": "Summary not found or not authorized to delete"},
                            status=status.HTTP_404_NOT_FOUND)