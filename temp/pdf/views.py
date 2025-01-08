import os
import redis

from rest_framework.response import Response
from rest_framework import status
from rest_framework.utils import json
from rest_framework.views import APIView
from swagger.file_upload_docs import pdf_upload_doc
from rest_framework.parsers import MultiPartParser
from temp.pdf.models import UploadedPDF
from temp.pdf.utils import extract_and_store_pdf_to_redis

# Redis 연결 설정
redis_client = redis.StrictRedis(host='redis', port=6379, db=0)


class PDFUploadView(APIView):
    """PDF 파일 업로드 및 텍스트 추출"""
    parser_classes = [MultiPartParser]
    @pdf_upload_doc
    def post(self, request):
        uploaded_file = request.FILES['file']
        file_instance = UploadedPDF(file=uploaded_file, file_name=uploaded_file.name)
        file_instance.save()

        # 임시 경로에 파일 저장
        pdf_path = f"/tmp/{uploaded_file.name}"
        with open(pdf_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # 텍스트 추출 및 Redis 저장
        try:
            total_pages = extract_and_store_pdf_to_redis(pdf_path, file_instance.id)
        except Exception as e:
            os.remove(pdf_path)
            file_instance.delete()
            return Response({"error": f"Failed to process PDF: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        os.remove(pdf_path)
        return Response({
            "message": "File uploaded and text extracted successfully",
            "file_id": file_instance.id,
            "total_pages": total_pages
        }, status=status.HTTP_201_CREATED)


class PDFPageTextView(APIView):
    """Redis에서 특정 PDF의 페이지 텍스트 확인"""
    def get(self, request, file_id, page_number):
        redis_key = f"pdf:{file_id}:page:{page_number}"
        text = redis_client.get(redis_key)
        if not text:
            return Response({"error": "Page not found"}, status=404)
        text = json.loads(text)  # JSON 문자열을 dict로 변환
        return Response({
            "page_number": text["page_number"],
            "text": text["text"]
        })
class PDFDeleteByFileIDView(APIView):
    """
    특정 file_id와 관련된 모든 Redis 데이터를 삭제
    """
    def delete(self, request, file_id):
        try:
            # 해당 file_id와 관련된 모든 키를 검색
            pattern = f"pdf:{file_id}:*"
            keys = redis_client.keys(pattern)

            # 키가 없을 경우 에러 반환
            if not keys:
                return Response({"message": f"No data found for file_id {file_id}"}, status=status.HTTP_404_NOT_FOUND)

            # 모든 키 삭제
            redis_client.delete(*keys)

            return Response({"message": f"All pages for file_id {file_id} have been deleted."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)