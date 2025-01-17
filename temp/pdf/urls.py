from django.urls import path
from .views import PDFUploadView, PDFPageTextView, PDFDeleteByFileIDView, PDFGenerateView
urlpatterns = [
    path('upload/', PDFUploadView.as_view(), name='file-upload'),
    path('<int:file_id>/page/<int:page_number>/', PDFPageTextView.as_view(), name='page-text'),
    path('delete/<int:file_id>/', PDFDeleteByFileIDView.as_view(), name='delete_file_data'),
    path('generate-summary-pdf/<str:redis_key>/', PDFGenerateView.as_view(), name='generate_summary_pdf'),
]
