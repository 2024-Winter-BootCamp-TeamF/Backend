from django.urls import path
from .views import hello_view
from .views import OpenAIView

urlpatterns = [
    path('hello/', hello_view, name='hello'),
    path('openai/', OpenAIView.as_view(), name='openai'),
]
