from django.urls import path
from .views import SummaryAPIView, DeleteUserDataView

urlpatterns = [
    path('summary/', SummaryAPIView.as_view(), name='summary'),
    path("delete/", DeleteUserDataView.as_view(), name="delete_user_data"),

]
