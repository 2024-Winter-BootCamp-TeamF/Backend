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
        operation_description="Pinecone에 저장된 모든 데이터를 요약합니다.",
        responses={
            202: openapi.Response("요약 작업이 성공적으로 시작되었습니다."),
        }
    )
    def post(self, request):
        """
        요약 작업을 시작하는 API 엔드포인트
        """
        # 사용자 ID 가져오기
        user_id = request.user.id

        # Celery 비동기 작업 호출
        task = process_summary_task.delay(user_id)

        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)
