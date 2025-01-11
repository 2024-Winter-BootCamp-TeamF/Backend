from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from temp.pdf.views import PDFUploadView

schema_view = get_schema_view(
    openapi.Info(
        title="File Upload API",
        default_version="v1",
        description="API for uploading files",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]