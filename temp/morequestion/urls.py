from django.urls import path
from .views import RegenerateQuestionsAPIView, DeleteMoreQuestionView, SubmitAnswerAPIView, DeleteUserAnswerView

urlpatterns = [
    path('create/', RegenerateQuestionsAPIView.as_view(), name='create-more'),
    path('submit-answer/', SubmitAnswerAPIView.as_view(), name='submit-answer'),
    path("more-questions/<int:question_id>/delete/", DeleteMoreQuestionView.as_view(), name="delete-more-question"),
    path("more-answers/<int:answer_id>/delete/", DeleteUserAnswerView.as_view(), name="delete-user-answer"),
]