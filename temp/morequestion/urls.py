from django.urls import path
from .views import RegenerateQuestionsAPIView, DeleteMoreQuestionView, SubmitAnswerAPIView, DeleteUserAnswerView, WrongAnswerView, AllQuestionsView

urlpatterns = [
    path('create/', RegenerateQuestionsAPIView.as_view(), name='create-more'),
    path('submit-answer/', SubmitAnswerAPIView.as_view(), name='submit-answer'),
    path("more-questions/<int:question_id>/delete/", DeleteMoreQuestionView.as_view(), name="delete-more-question"),
    path("more-answers/<int:answer_id>/delete/", DeleteUserAnswerView.as_view(), name="delete-user-answer"),
    path('incorrect-answers/', WrongAnswerView.as_view(), name='incorrect_answers_api'),
    path('all-questions/', AllQuestionsView.as_view(), name='all_questions_api'),
]