import redis
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .openaiService import generate_summary, generate_problem
from temp.models import Summary, Problem  # MySQL 모델 가져오기

# Redis 클라이언트 설정
redis_client = redis.StrictRedis(host="redis", port=6379, db=0)


class ProcessRedisDataView(APIView):
    """
    Redis 데이터를 처리하여 요약 또는 문제를 생성하는 API
    """

    @swagger_auto_schema(
        operation_description="Process the file by action type",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'file_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the file to process'),
                'action': openapi.Schema(type=openapi.TYPE_STRING, description="'summary' or 'problem'")
            },
            required=['file_id', 'action']
        ),
        responses={
            200: openapi.Response(description="Processing successful"),
            400: openapi.Response(description="Invalid JSON input"),
            500: openapi.Response(description="Internal server error"),
        }
    )
    def post(self, request):
        file_id = request.data.get("file_id")
        action = request.data.get("action")

        if not file_id or not action:
            return Response({"error": "file_id and action are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Redis에서 데이터 가져오기
        keys = redis_client.keys(f"pdf:{file_id}:page:*")
        if not keys:
            return Response({"error": "No data found for the given file_id"}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Redis 데이터를 하나의 텍스트로 합치기
            full_text = ""
            for key in sorted(keys):
                page_data = redis_client.get(key)
                if not page_data:
                    continue
                page_text = page_data.decode('utf-8')
                full_text += page_text + "\n"

            # Action 처리
            if action == "summary":
                result = generate_summary(full_text)
                if result["success"]:
                    # 요약 결과를 MySQL에 저장
                    Summary.objects.create(pdf_file_id=file_id, summary_text=result["response"])
                    return Response({"message": "요약완료", "result": result["response"]}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": result["error"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            elif action == "problem":
                result = generate_problem(full_text)
                if result["success"]:
                    # 문제 결과를 MySQL에 저장
                    Problem.objects.create(pdf_file_id=file_id, problem_text=result["response"], problem_type="Generated")
                    return Response({"message": "문제생성 완료", "result": result["response"]}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": result["error"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            else:
                return Response({"error": "Invalid action. Use 'summary' or 'problem'."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": f"Failed to process: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
