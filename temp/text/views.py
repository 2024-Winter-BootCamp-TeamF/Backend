from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated
from .tasks import upload_to_pinecone_task


class UploadToPineconeView(APIView):
    """
    Redis 데이터를 Pinecone에 업로드하는 API
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Upload all Redis data to Pinecone asynchronously.",
        responses={
            202: openapi.Response(
                description="Data upload task started successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "task_id": openapi.Schema(type=openapi.TYPE_STRING),
                    }
                ),
            ),
            500: "Internal server error.",
        }
    )
    def post(self, request):
        user_id = request.user.id  # 인증된 사용자 ID 가져오기
        task = upload_to_pinecone_task.delay(user_id)  # 비동기 작업 호출

        return Response(
            {
                "message": "Data upload task started successfully.",
                "task_id": task.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )
