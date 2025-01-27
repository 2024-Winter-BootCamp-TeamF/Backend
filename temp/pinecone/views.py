import os
import redis
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from collections import defaultdict
from .tasks import upload_file_id_to_pinecone_task
from .service import (
    get_pinecone_instance,
    query_pinecone_data
)
from temp.openaiService import get_embedding

# Redis 클라이언트 설정
redis_client = redis.StrictRedis(host="redis", port=6379, db=0)


class UploadAllToPineconeView(APIView):
    """
    모든 Redis 데이터를 Pinecone에 업로드하는 API
    """
    permission_classes = [IsAuthenticated]  # 토큰 인증 필요

    @swagger_auto_schema(
        operation_description="Upload all Redis data to Pinecone",
        responses={
            200: openapi.Response(description="All data uploaded successfully"),
            500: openapi.Response(description="Internal server error"),
        }
    )
    def post(self, request):
        try:
            # 사용자 ID 가져오기
            user_id = request.user.id

            # Redis에서 모든 키 가져오기
            keys = redis_client.keys("pdf:*:page:*")
            if not keys:
                return Response({"error": "No data found in Redis."}, status=status.HTTP_404_NOT_FOUND)

            # file_id별로 키 그룹화
            file_id_map = defaultdict(list)
            for key in keys:
                key_str = key.decode("utf-8")  # Redis 키는 바이트 형식이므로 문자열로 변환
                parts = key_str.split(":")
                file_id = parts[1]  # `pdf:<file_id>:page:<page_number>` 중 file_id 추출
                file_id_map[file_id].append(key_str)

            # 각 file_id별로 비동기 작업 실행
            tasks = []
            for file_id, file_keys in file_id_map.items():
                task = upload_file_id_to_pinecone_task.delay(file_id, file_keys, user_id)
                tasks.append({"file_id": file_id, "task_id": task.id})

            return Response({
                "message": "File ID-based upload tasks started.",
                "tasks": tasks  # 실행된 태스크 목록 반환
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response({"error": f"Failed to start upload tasks: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QueryFromPineconeView(APIView):
    """
    Pinecone에서 특정 데이터를 조회하는 API
    """

    query_param = openapi.Parameter(
        "redis_key", openapi.IN_QUERY, description="Redis에서 저장된 키", type=openapi.TYPE_STRING
    )

    @swagger_auto_schema(
        operation_description="Query specific data from Pinecone by Redis key",
        manual_parameters=[query_param],
        responses={
            200: openapi.Response(description="Query successful", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "id": openapi.Schema(type=openapi.TYPE_STRING, description="Pinecone record ID"),
                    "values": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_NUMBER)),
                    "metadata": openapi.Schema(type=openapi.TYPE_OBJECT, description="Metadata associated with the record")
                }
            )),
            404: openapi.Response(description="Data not found"),
            500: openapi.Response(description="Internal server error"),
        }
    )
    def get(self, request):
        redis_key = request.query_params.get("redis_key")
        if not redis_key:
            return Response({"error": "Missing 'redis_key' query parameter."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = request.user.id  # 사용자 ID 가져오기
            instance = get_pinecone_instance()
            index_name = os.getenv("PINECONE_INDEX_NAME", "pdf-index")
            data = query_pinecone_data(instance, index_name, redis_key, user_id)  # user_id 추가

            if not data:
                return Response({"error": "Data not found for the given Redis key."}, status=status.HTTP_404_NOT_FOUND)

            return Response({
                "id": redis_key,
                "values": data.get("values"),
                "metadata": data.get("metadata")  # 메타데이터 반환
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Failed to query Pinecone: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

