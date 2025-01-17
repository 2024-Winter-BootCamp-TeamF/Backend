import os
import redis
import subprocess
import logging
from rest_framework.response import Response
from rest_framework import status
from rest_framework.utils import json
from rest_framework.views import APIView
from swagger.file_upload_docs import pdf_upload_doc
from fpdf import FPDF
from PIL import Image
from rest_framework.parsers import MultiPartParser
from temp.pdf.models import UploadedPDF
from temp.pdf.utils import extract_and_store_pdf_to_redis, pdf_to_text
from django.http import FileResponse, Http404
from temp.pinecone.models import PineconeSummary

# Redis 연결 설정
redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

logger = logging.getLogger(__name__)

class PDFUploadView(APIView):
    """PDF 파일 업로드 및 텍스트 추출"""
    parser_classes = [MultiPartParser]
    @pdf_upload_doc
    def post(self, request):

        if 'file' not in request.FILES:
            return Response({"error": "파일을 업로드해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name
        file_extension = os.path.splitext(file_name)[1].lower()

        # 파일이 pdf인 경우
        if file_extension == '.pdf':
            # 임시 경로에 파일 저장
            pdf_path = f"/tmp/{file_name}"
            self.local_file_upload(pdf_path, uploaded_file)

            file_instance = UploadedPDF(file=uploaded_file, file_name=file_name)
            file_instance.save()

            # 텍스트 추출 및 Redis 저장
            try:
                total_pages = extract_and_store_pdf_to_redis(pdf_path, file_instance.id)
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
            self.local_file_upload(temp_file_path, uploaded_file)

            # 2. 파일 변환
            try:
                if file_extension == '.pptx':
                    self.ppt_to_pdf(temp_file_path, output_pdf_path)
                elif file_extension == '.docx':
                    self.word_to_pdf(temp_file_path, output_pdf_path)
                elif file_extension in ['.jpg', '.jpeg', '.png']:
                    self.image_to_pdf(temp_file_path, output_pdf_path)
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
                total_pages = extract_and_store_pdf_to_redis(output_pdf_path, file_instance.id)
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


    def local_file_upload(self, file_path, uploaded_file):
        try:
            with open(file_path, 'wb') as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
            logger.info(f"파일 저장 완료: {file_path}")
        except Exception as e:
            logger.error(f"파일 저장 실패: {str(e)}")
            return Response({"error": f"파일 저장 실패: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def ppt_to_pdf(self, input_path, output_path):
        try:
            subprocess.run([
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                os.path.dirname(output_path),
                input_path
            ], check=True)
            logger.info(f"LibreOffice를 사용한 PPT -> PDF 변환 완료: {output_path}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"LibreOffice 변환 실패: {str(e)}")

    def word_to_pdf(self, input_path, output_path):
        try:
            # LibreOffice를 headless 모드로 실행하여 .docx 파일을 .pdf로 변환
            subprocess.run([
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                os.path.dirname(output_path),
                input_path
            ], check=True)
            logger.info(f"LibreOffice를 사용한 Word -> PDF 변환 완료: {output_path}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"LibreOffice 변환 실패: {str(e)}")

    def image_to_pdf(self, input_path, output_path):
        image = Image.open(input_path)
        pdf = FPDF()
        pdf.add_page()

        image_width, image_height = image.size
        aspect_ratio = image_height / image_width
        pdf_width = 210  # A4 크기 (mm)
        pdf_height = pdf_width * aspect_ratio

        temp_image_path = "/tmp/temp_image.jpg"
        image.save(temp_image_path)

        pdf.image(temp_image_path, x=0, y=0, w=pdf_width, h=pdf_height)
        os.remove(temp_image_path)

        pdf.output(output_path)


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

