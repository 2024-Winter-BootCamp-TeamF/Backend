from django.urls import path
from .views import PDFUploadView, PDFPageTextView, PDFDeleteByFileIDView, PDFGenerateView, GenealogyUploadView
urlpatterns = [
    path('upload', PDFUploadView.as_view(), name='file-upload'),
    path('genealogy-upload', GenealogyUploadView.as_view(), name='file-upload'),
    #path('<int:file_id>/page/<int:page_number>/', PDFPageTextView.as_view(), name='page-text'),
    path('delete/<int:file_id>', PDFDeleteByFileIDView.as_view(), name='delete_file_data'),
    #path('summary-pdf/<str:redis_key>/', PDFGenerateView.as_view(), name='summary_pdf'),
]
