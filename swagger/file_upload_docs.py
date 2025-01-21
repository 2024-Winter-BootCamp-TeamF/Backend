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
