from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

pdf_upload_doc = swagger_auto_schema(
    operation_description="Upload a PDF file, extract text, and save to Redis.",
    manual_parameters=[
        openapi.Parameter(
            'file',
            openapi.IN_FORM,
            description="The PDF file to upload",
            type=openapi.TYPE_FILE,
            required=True
        ),
    ],
    responses={
        201: openapi.Response("File uploaded and text extracted successfully"),
        400: openapi.Response("No file provided"),
        401: openapi.Response("Unauthorized: Token is missing or invalid"),
        500: openapi.Response("Failed to process PDF"),
    }
)

genealogy_upload_doc = swagger_auto_schema(
    operation_description="PDF 파일을 업로드하고, 텍스트를 추출하여 Redis에 저장합니다.",
    manual_parameters=[
        openapi.Parameter(
            'file',
            openapi.IN_FORM,
            description="업로드할 PDF 파일 (선택사항)",
            type=openapi.TYPE_FILE,
            required=False  # 파일은 선택사항
        ),
        openapi.Parameter(
            'text',
            openapi.IN_FORM,
            description="파일과 함께 저장할 추가 텍스트 (선택사항)",
            type=openapi.TYPE_STRING,
            required=False,  # 텍스트는 선택사항
        ),
    ],
    responses={
        201: openapi.Response("파일이 업로드되고 텍스트가 성공적으로 추출되었습니다."),
        400: openapi.Response("파일이 제공되지 않았습니다."),
        401: openapi.Response("인증 실패: 토큰이 없거나 유효하지 않습니다."),
        500: openapi.Response("PDF 처리에 실패했습니다."),
    }
)
