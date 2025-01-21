import os
import redis
import logging
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.utils import json
from rest_framework.views import APIView
from swagger.file_upload_docs import pdf_upload_doc, genealogy_upload_doc
from rest_framework.parsers import MultiPartParser
from temp.pdf.models import UploadedPDF
from temp.pdf.utils import (extract_and_store_pdf_to_redis,
                            pdf_to_text, local_file_upload, extract_and_store_text_to_redis, ppt_to_pdf, word_to_pdf, image_to_pdf)
from django.http import FileResponse, Http404
from temp.pinecone.models import PineconeSummary
import uuid
from rest_framework.permissions import IsAuthenticated

# Redis 연결 설정
redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

logger = logging.getLogger(__name__)

class PDFUploadView(APIView):
    """PDF 파일 업로드 및 텍스트 추출"""
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능
    parser_classes = [MultiPartParser]  # 파일 업로드를 처리

    @pdf_upload_doc
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)


        if 'file' not in request.FILES:
            return Response({"error": "파일을 업로드해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name
        file_extension = os.path.splitext(file_name)[1].lower()

        # 파일이 pdf인 경우
        if file_extension == '.pdf':
            # 임시 경로에 파일 저장
            pdf_path = f"/tmp/{file_name}"
            local_file_upload(pdf_path, uploaded_file)

            # PDF 객체 생성 및 저장
            file_instance = UploadedPDF(
                file=uploaded_file,
                file_name=file_name,
                user=request.user  # 현재 요청한 사용자 정보 추가
            )
            file_instance.save()

            # 텍스트 추출 및 Redis 저장
            try:
                total_pages = extract_and_store_pdf_to_redis(pdf_path, file_instance.id, file_name)
            except Exception as e:
                os.remove(pdf_path)
                file_instance.delete()
                return Response({"error": f"Failed to process PDF: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            os.remove(pdf_path)
            return Response({
                "message": "File uploaded and text extracted successfully",
                "file_id": file_instance.id,
                "total_pages": total_pages
            }, status=status.HTTP_201_CREATED)

        else :
            temp_file_path = f"/tmp/{file_name}"
            output_pdf_path = f"/tmp/{os.path.splitext(file_name)[0]}.pdf"

            # 1. 업로드된 파일을 로컬에 저장
            local_file_upload(temp_file_path, uploaded_file)

            # 2. 파일 변환
            try:
                if file_extension == '.pptx':
                    ppt_to_pdf(temp_file_path, output_pdf_path)
                elif file_extension == '.docx':
                    word_to_pdf(temp_file_path, output_pdf_path)
                elif file_extension in ['.jpg', '.jpeg', '.png']:
                    image_to_pdf(temp_file_path, output_pdf_path)
                else:
                    return Response({"error": "지원되지 않는 파일 형식입니다."}, status=status.HTTP_400_BAD_REQUEST)
                logger.info(f"PDF 변환 완료: {output_pdf_path}")
            except Exception as e:
                logger.error(f"파일 변환 실패: {str(e)}")
                return Response({"error": f"파일 변환 실패: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

            file_instance = UploadedPDF(file=output_pdf_path, file_name=file_name)
            file_instance.save()

            # 텍스트 추출 및 Redis 저장
            try:
                total_pages = extract_and_store_pdf_to_redis(output_pdf_path, file_instance.id, file_name)
            except Exception as e:
                os.remove(output_pdf_path)
                file_instance.delete()
                return Response({"error": f"Failed to process PDF: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            os.remove(output_pdf_path)
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
          
class PDFGenerateView(APIView):
    """
    MySQL에서 텍스트 데이터를 가져와 PDF로 변환해 반환
    """
    def get(self, request, redis_key):
        try:
            # MySQL에서 해당 redis_key와 관련된 데이터 가져오기
            summary_instance = PineconeSummary.objects.get(redis_key=redis_key)
            summary_text = summary_instance.summary_text  # 요약본 가져오기

            if not summary_text:
                raise Http404("Summary text not found.")

            # PDF 생성
            pdf_buffer = pdf_to_text(summary_text)

            # PDF 반환
            return FileResponse(pdf_buffer, as_attachment=True, filename=f"{redis_key}_summary.pdf")

        except PineconeSummary.DoesNotExist:
            return Response({"error": "Summary not found for the given redis_key."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class GenealogyUploadView(APIView):
    """족보 파일 업로드 및 텍스트 저장"""
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능
    parser_classes = [MultiPartParser]  # 파일 업로드를 처리

    @genealogy_upload_doc
    def post(self, request):
        uploaded_file = request.FILES.get('file', None)
        text = request.data.get('text', None)  # 텍스트 값 가져오기

        # 파일 업로드 처리
        if uploaded_file:
            file_name = uploaded_file.name

            # 파일 이름에 "족보" 추가
            if "족보" not in file_name:
                base_name, extension = os.path.splitext(file_name)
                file_name = f"{base_name}_족보{extension}"

            file_instance = UploadedPDF(file=uploaded_file, file_name=file_name)
            file_instance.save()

            # 임시 경로에 파일 저장
            pdf_path = f"/tmp/{file_name}"
            local_file_upload(pdf_path, uploaded_file)

            # 텍스트 추출 및 Redis 저장
            try:
                total_pages = extract_and_store_pdf_to_redis(pdf_path, file_instance.id, file_name)
            except Exception as e:
                os.remove(pdf_path)
                file_instance.delete()
                return Response({"error": f"Failed to process PDF: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            os.remove(pdf_path)

            return Response({
                "message": "File uploaded and text extracted successfully",
                "file_id": file_instance.id,
                "file_name": file_name,
                "total_pages": total_pages
            }, status=status.HTTP_201_CREATED)

        # 텍스트만 저장 처리
        elif text:
            # Redis에 텍스트 저장
            file_id = f"text_only_{uuid.uuid4()}"  # 텍스트에 대한 고유 ID 생성
            total_lines = extract_and_store_text_to_redis(text, file_id, "text_only_족보")

            return Response({
                "message": "Text extracted and stored successfully",
                "file_id": file_id,
                "file_name": "text_only_족보",
                "total_lines": total_lines
            }, status=status.HTTP_201_CREATED)

        # 파일이나 텍스트가 모두 없는 경우
        return Response({"error": "파일이나 텍스트를 업로드해주세요."}, status=status.HTTP_400_BAD_REQUEST)
