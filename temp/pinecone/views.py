import os
import redis
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .service import get_pinecone_index, get_pinecone_instance, query_pinecone_data, query_pinecone_original_text, process_and_save_summary
from temp.openaiService import get_embedding

# Redis 클라이언트 설정
redis_client = redis.StrictRedis(host="redis", port=6379, db=0)


class UploadAllToPineconeView(APIView):
    """
    모든 Redis 데이터를 Pinecone에 업로드하는 API
    """
    @swagger_auto_schema(
        operation_description="Upload all Redis data to Pinecone",
        responses={
            200: openapi.Response(description="All data uploaded successfully"),
            500: openapi.Response(description="Internal server error"),
        }
    )

    def post(self, request):
        try:
            # Redis 데이터 처리 및 Pinecone 업로드
            keys = redis_client.keys("pdf:*:page:*")
            if not keys:
                return Response({"error": "No data found in Redis."}, status=status.HTTP_404_NOT_FOUND)

            instance = get_pinecone_instance()
            index_name = os.getenv("PINECONE_INDEX_NAME", "pdf-index")
            index = get_pinecone_index(instance, index_name)

            for key in sorted(keys):
                page_data = redis_client.get(key)
                if not page_data:
                    continue

                try:
                    # Redis에서 데이터 로드
                    page_content = json.loads(page_data.decode('utf-8'))
                    text_field = page_content.get("text")
                    file_name = page_content.get("file_name", "unknown")  # 파일 이름 기본값 설정

                    # 텍스트 처리
                    if isinstance(text_field, dict) and "text" in text_field:
                        text = text_field["text"]
                    elif isinstance(text_field, str):
                        text = text_field
                    else:
                        raise ValueError(f"Invalid 'text' format in Redis data for key {key}")

                    # 벡터 생성
                    vector = get_embedding(text)

                    # Pinecone에 업로드
                    index.upsert([
                        (
                            key.decode('utf-8'),  # Redis 키를 ID로 사용
                            vector,  # 생성된 벡터
                            {  # 메타데이터
                                "page_number": page_content.get("page_number"),
                                "file_name": file_name,  # 파일 제목 저장
                                "original_text": text,  # 원본 텍스트 저장
                                "category": self.determine_category(file_name),  # 파일 이름 기반 카테고리
                            }
                        )
                    ])

                except Exception as e:
                    print(f"Failed to process key {key}: {str(e)}")
                    continue

            # Redis 데이터 전체 삭제
            redis_client.flushdb()

            return Response({"message": "All data uploaded to Pinecone successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Failed to upload to Pinecone: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def determine_category(self, file_name):
        """
        파일 이름을 기반으로 카테고리를 결정합니다.
        """
        lecture_keywords = ["족보", "수시", "중간", "기말", "고사", "quiz", "퀴즈"]
        file_name_lower = file_name.lower()  # 파일 이름 소문자로 변환

        # 파일 이름에 강의 자료 키워드가 포함되어 있는지 확인
        if any(keyword in file_name_lower for keyword in lecture_keywords):
            return "genealogy" # 족보

        # 기본 카테고리
        return "lecture_notes" # 강의 자료

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
            instance = get_pinecone_instance()
            index_name = os.getenv("PINECONE_INDEX_NAME", "pdf-index")
            data = query_pinecone_data(instance, index_name, redis_key)

            if not data:
                return Response({"error": "Data not found for the given Redis key."}, status=status.HTTP_404_NOT_FOUND)

            return Response({
                "id": redis_key,
                "values": data.get("values"),
                "metadata": data.get("metadata")  # 메타데이터 반환
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Failed to query Pinecone: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GenerateAndSaveSummaryView(APIView):
    """
    Pinecone에서 텍스트를 조회, 요약하고 MySQL에 저장하는 API
    """

    query_param = openapi.Parameter(
        "redis_key", openapi.IN_QUERY, description="Redis에서 저장된 키", type=openapi.TYPE_STRING
    )

    @swagger_auto_schema(
        operation_description="Generate summary from Pinecone and save to MySQL",
        manual_parameters=[query_param],
        responses={
            200: openapi.Response(description="Summary created and saved successfully."),
            404: openapi.Response(description="Original text not found."),
            500: openapi.Response(description="Internal server error."),
        }
    )
    def get(self, request):
        redis_key = request.query_params.get("redis_key")
        if not redis_key:
            return Response({"error": "Missing 'redis_key' query parameter."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Pinecone 인스턴스 생성 및 텍스트 가져오기
            instance = get_pinecone_instance()
            index_name = os.getenv("PINECONE_INDEX_NAME", "pdf-index")
            original_text = query_pinecone_original_text(instance, index_name, redis_key)

            if not original_text:
                return Response({"error": "Original text not found for the given Redis key."}, status=status.HTTP_404_NOT_FOUND)

            # 요약 생성 및 저장
            summary = process_and_save_summary(redis_key, original_text)

            return Response({
                "message": "Summary created and saved successfully.",
                "summary": summary,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Failed to process request: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

