from django.urls import path
from . import views
from .views import TranslateAPIView

urlpatterns = [
    path("translate/", TranslateAPIView.as_view(), name="translate"),
]
