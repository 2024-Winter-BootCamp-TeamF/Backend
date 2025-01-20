from django.urls import path
from .views import UploadAllToPineconeView

urlpatterns = [
    path("pinecone/", UploadAllToPineconeView.as_view(), name="pinecone"),
]


