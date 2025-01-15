import os

import redis
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .service import get_pinecone_index, store_in_pinecone, get_pinecone_instance, list_all_indexes, list_ids_in_index, fetch_from_pinecone_by_id
from ..openaiService import get_embedding

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
                    page_content = json.loads(page_data.decode('utf-8'))
                    text_field = page_content.get("text")

                    if isinstance(text_field, dict) and "text" in text_field:
                        text = text_field["text"]
                    elif isinstance(text_field, str):
                        text = text_field
                    else:
                        raise ValueError(f"Invalid 'text' format in Redis data for key {key}")

                    vector = get_embedding(text)
                    index.upsert([(key.decode('utf-8'), vector, {"page_number": page_content["page_number"]})])

                except Exception as e:
                    print(f"Failed to process key {key}: {str(e)}")
                    continue

            return Response({"message": "All data uploaded to Pinecone successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Failed to upload to Pinecone: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ListAllIndexesView(APIView):
    """
    Pinecone에 저장된 모든 인덱스 이름을 반환하는 API
    """

    @swagger_auto_schema(
        operation_description="List all Pinecone indexes",
        responses={
            200: openapi.Response(description="Indexes retrieved successfully", schema=openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING))),
            500: openapi.Response(description="Internal server error")
        }
    )
    def get(self, request):
        try:
            instance = get_pinecone_instance()
            indexes = list_all_indexes(instance)
            if isinstance(indexes, dict) and "error" in indexes:
                return Response(indexes, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(indexes, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to retrieve indexes: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ListIDsInIndexView(APIView):
    """
    특정 Pinecone 인덱스의 모든 ID를 반환하는 API
    """

    @swagger_auto_schema(
        operation_description="List all IDs in a specific Pinecone index",
        manual_parameters=[
            openapi.Parameter('index_name', openapi.IN_QUERY, description="The name of the Pinecone index", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: openapi.Response(description="IDs retrieved successfully", schema=openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING))),
            404: openapi.Response(description="Index not found"),
            500: openapi.Response(description="Internal server error")
        }
    )
    def get(self, request):
        index_name = request.query_params.get('index_name')
        if not index_name:
            return Response({"error": "index_name parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            instance = get_pinecone_instance()
            ids = list_ids_in_index(instance, index_name)
            if isinstance(ids, dict) and "error" in ids:
                return Response(ids, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(ids, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to retrieve IDs: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FetchDataByIDView(APIView):
    """
    특정 ID로 Pinecone에서 데이터를 조회하는 API
    """

    @swagger_auto_schema(
        operation_description="Fetch data by ID from a specific Pinecone index",
        manual_parameters=[
            openapi.Parameter('index_name', openapi.IN_QUERY, description="The name of the Pinecone index", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('doc_id', openapi.IN_QUERY, description="The document ID to fetch", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: openapi.Response(description="Data retrieved successfully", schema=openapi.Schema(type=openapi.TYPE_OBJECT)),
            404: openapi.Response(description="ID not found"),
            500: openapi.Response(description="Internal server error")
        }
    )
    def get(self, request):
        index_name = request.query_params.get('index_name')
        doc_id = request.query_params.get('doc_id')
        if not index_name or not doc_id:
            return Response({"error": "index_name and doc_id parameters are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            instance = get_pinecone_instance()
            data = fetch_from_pinecone_by_id(instance, index_name, doc_id)
            if isinstance(data, str) and "Error" in data:
                return Response({"error": data}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            if isinstance(data, str) and "No data" in data:
                return Response({"error": data}, status=status.HTTP_404_NOT_FOUND)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to fetch data: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

