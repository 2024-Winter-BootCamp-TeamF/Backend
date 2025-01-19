from django.urls import path
from .views import UploadAllToPineconeView

urlpatterns = [
    path("save/", UploadAllToPineconeView.as_view(), name="pinecone"),
]


