from django.urls import path
from .views import TopicsAndQuestionsRAGView, SubmitAnswerAPIView, RegenerateQuestionsAPIView

urlpatterns = [
    path('create/', TopicsAndQuestionsRAGView.as_view(), name='create'),
    path('submit-answer/', SubmitAnswerAPIView.as_view(), name='submit-answer'),
    path('create-more/', RegenerateQuestionsAPIView.as_view(), name='create-more'),
]