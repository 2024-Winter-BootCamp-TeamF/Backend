from django.urls import path
from .views import UploadAllToPineconeView, QueryFromPineconeView

urlpatterns = [
    path("upload/", UploadAllToPineconeView.as_view(), name="upload-to-pinecone"),
    #path("query/", QueryFromPineconeView.as_view(), name="query-pinecone"),
]
