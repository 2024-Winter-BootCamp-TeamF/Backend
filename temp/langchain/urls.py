from django.urls import path
from .views import SummaryAPIView, DeleteUserDataView, DeleteSummaryView

urlpatterns = [
    path('summary', SummaryAPIView.as_view(), name='summary'),
    path("delete", DeleteUserDataView.as_view(), name="delete_user_data"),
    path("summary/<int:summary_id>/delete", DeleteSummaryView.as_view(), name="delete-summary"),

]
