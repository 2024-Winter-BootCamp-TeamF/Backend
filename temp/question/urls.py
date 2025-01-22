from django.urls import path
from .views import TopicsAndQuestionsRAGView, SubmitAnswerAPIView, DeleteQuestionView, DeleteUserAnswerView, WrongAnswerView, AllQuestionsView

urlpatterns = [
    path('create/', TopicsAndQuestionsRAGView.as_view(), name='create'),
    path('submit-answer/', SubmitAnswerAPIView.as_view(), name='submit-answer'),
    path("questions/<int:question_id>/delete/", DeleteQuestionView.as_view(), name="delete-question"),
    path("answers/<int:answer_id>/delete/", DeleteUserAnswerView.as_view(), name="delete-user-answer"),
    path('api/incorrect-answers/', WrongAnswerView.as_view(), name='incorrect_answers_api'),
    path('api/all-questions/', AllQuestionsView.as_view(), name='all_questions_api'),

]