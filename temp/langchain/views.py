from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .tasks import process_summary_task
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

        # 비동기 Celery 작업 호출 (각 topic에 대해 개별 작업 실행)
        task_ids = []
        for topic in topics:
            task = process_summary_task.delay(user_id, topic)
            task_ids.append(task.id)

        return Response({
            "message": "Summary generation tasks started successfully.",
            "task_ids": task_ids,  # 각 작업의 ID 반환
        }, status=status.HTTP_202_ACCEPTED)
