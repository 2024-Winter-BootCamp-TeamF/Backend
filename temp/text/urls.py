from django.urls import path
from .views import UploadToPineconeView

urlpatterns = [
    path("celery-upload", UploadToPineconeView.as_view(), name="celery-upload"),
]
