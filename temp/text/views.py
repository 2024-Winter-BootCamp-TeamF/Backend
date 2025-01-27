from .tasks import upload_redis_to_pinecone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class UploadAllToPineconeView(APIView):
    """
    모든 Redis 데이터를 Pinecone에 업로드하는 API
    """
    permission_classes = [IsAuthenticated]  # 토큰 인증 필요

    @swagger_auto_schema(
        operation_description="모든 Redis 데이터를 Pinecone에 업로드하는 API",
        responses={
            202: openapi.Response(description="Task to upload all data started successfully"),
            500: openapi.Response(description="Internal server error"),
        }
    )
    def post(self, request):
        try:
            # 사용자 ID 가져오기
            user_id = request.user.id  # 인증된 사용자 ID

            # Celery 비동기 작업 호출
            task = upload_redis_to_pinecone.delay(user_id)

            return Response({
                "message": "Task to upload all Redis data to Pinecone started successfully.",
                "task_id": task.id  # 작업 ID 반환
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response({"error": f"Failed to start task: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
