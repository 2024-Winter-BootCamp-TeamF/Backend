from django.urls import path
from .views import TopicsAndQuestionsRAGView, SubmitAnswerAPIView

urlpatterns = [
    path('<int:file_id>/page/<int:page_number>/', TopicsAndQuestionsRAGView.as_view(), name='page-text'),
    path('<int:question_id>/submit-answer/<str:user_answer>/', SubmitAnswerAPIView.as_view(), name='submit-answer'),
]