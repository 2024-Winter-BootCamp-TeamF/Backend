from django.urls import path
from .views import TopicsAndQuestionsRAGView, SubmitAnswerAPIView, RegenerateQuestionsAPIView, DeleteQuestionView, \
    DeleteUserAnswerView, DeleteMoreQuestionView

urlpatterns = [
    path('create/', TopicsAndQuestionsRAGView.as_view(), name='create'),
    path('submit-answer/', SubmitAnswerAPIView.as_view(), name='submit-answer'),
    path('create-more/', RegenerateQuestionsAPIView.as_view(), name='create-more'),
    path("questions/<int:question_id>/delete/", DeleteQuestionView.as_view(), name="delete-question"),
    path("answers/<int:answer_id>/delete/", DeleteUserAnswerView.as_view(), name="delete-user-answer"),
    path("more-questions/<int:question_id>/delete/", DeleteMoreQuestionView.as_view(), name="delete-more-question"),

]