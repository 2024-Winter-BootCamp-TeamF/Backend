from django.urls import path
from .views import (TopicsAndQuestionsRAGView, SubmitAnswerAPIView, DeleteQuestionView,
                    DeleteUserAnswerView, WrongAnswerView, AllQuestionsView, ConfusedAnswerView)

urlpatterns = [
    path('create/', TopicsAndQuestionsRAGView.as_view(), name='create'),
    path('submit-answer/', SubmitAnswerAPIView.as_view(), name='submit-answer'),
    path("questions/<int:question_id>/delete/", DeleteQuestionView.as_view(), name="delete-question"),
    path("answers/<int:answer_id>/delete/", DeleteUserAnswerView.as_view(), name="delete-user-answer"),
    path('incorrect-answers/', WrongAnswerView.as_view(), name='incorrect_answers_api'),
    path('all-questions/', AllQuestionsView.as_view(), name='all_questions_api'),
    path('confused-answers/', ConfusedAnswerView.as_view(), name='confused_answers_api'),

]