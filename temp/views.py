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
        operation_description="Process multiple files by action type",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'file_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_INTEGER),
                    description='List of file IDs to process'
                ),
                'action': openapi.Schema(type=openapi.TYPE_STRING, description="'summary' or 'problem'")
            },
            required=['file_ids', 'action']
        ),
        responses={
            200: openapi.Response(description="Processing successful"),
            400: openapi.Response(description="Invalid JSON input"),
            500: openapi.Response(description="Internal server error"),
        }
    )
    def post(self, request):
        file_ids = request.data.get("file_ids")
        action = request.data.get("action")

        if not file_ids or not isinstance(file_ids, list):
            return Response({"error": "file_ids must be a list of integers"}, status=status.HTTP_400_BAD_REQUEST)
        if not action:
            return Response({"error": "action is required"}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        errors = []

        for file_id in file_ids:
            try:
                # Redis에서 데이터 가져오기
                keys = redis_client.keys(f"pdf:{file_id}:page:*")
                if not keys:
                    errors.append({"file_id": file_id, "error": "No data found for the given file_id"})
                    continue

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
                        results.append({"file_id": file_id, "summary": result["response"]})
                    else:
                        errors.append({"file_id": file_id, "error": result["error"]})

                elif action == "problem":
                    result = generate_problem(full_text)
                    if result["success"]:
                        # 문제 결과를 MySQL에 저장
                        Problem.objects.create(pdf_file_id=file_id, problem_text=result["response"], problem_type="Generated")
                        results.append({"file_id": file_id, "problem": result["response"]})
                    else:
                        errors.append({"file_id": file_id, "error": result["error"]})

                else:
                    errors.append({"file_id": file_id, "error": "Invalid action. Use 'summary' or 'problem'."})

            except Exception as e:
                errors.append({"file_id": file_id, "error": str(e)})

        return Response({
            "results": results,
            "errors": errors
        }, status=status.HTTP_200_OK)