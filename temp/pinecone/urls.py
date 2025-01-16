from django.urls import path
from .views import UploadAllToPineconeView, QueryFromPineconeView, GenerateAndSaveSummaryView

urlpatterns = [
    path("upload/", UploadAllToPineconeView.as_view(), name="upload-to-pinecone"),
    path("query/", QueryFromPineconeView.as_view(), name="query-pinecone"),
    path("summary/", GenerateAndSaveSummaryView.as_view(), name="summary"),
]
