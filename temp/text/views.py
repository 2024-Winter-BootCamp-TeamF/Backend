import os
import redis
import json
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .services import (
    get_pinecone_index,
    get_pinecone_instance,
    query_pinecone_data,
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
            user_id = request.user.id  # 인증된 사용자 ID

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
                    page_content = json.loads(page_data.decode("utf-8"))
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
                            f"{key.decode('utf-8')}",  # Redis 키를 사용한 데이터 ID
                            vector,  # 생성된 벡터
                            {  # 메타데이터
                                "page_number": page_content.get("page_number"),
                                "file_name": file_name,
                                "original_text": text,
                                "category": self.determine_category(file_name),
                                "user_id": user_id,  # 사용자 ID 추가
                            }
                        )
                    ], namespace=str(user_id))

                except Exception as e:
                    print(f"Failed to process key {key}: {str(e)}")
                    continue

            # Redis 데이터 전체 삭제
            redis_client.flushdb()

            return Response({"message": "All data uploaded to Pinecone successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Failed to upload to Pinecone: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def determine_category(self, file_name):
        """
        파일 이름을 기반으로 카테고리를 결정합니다.
        """
        lecture_keywords = ["족보", "수시", "중간", "기말", "고사", "quiz", "퀴즈"]
        file_name_lower = file_name.lower()  # 파일 이름 소문자로 변환

        if any(keyword in file_name_lower for keyword in lecture_keywords):
            return "genealogy"  # 족보

        return "lecture_notes"  # 기본값

