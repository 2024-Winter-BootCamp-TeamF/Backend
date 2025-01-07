from django.urls import path
from .views import hello_view

from . import views

urlpatterns = [
    path('hello/', hello_view, name='hello'),
    path('', views.item_list, name='item_list'),
    #path('<int:pk>/', views.item_detail, name='item_detail'),
    path('create/', views.item_create, name='item_create'),
    path('<int:pk>/update/', views.item_update, name='item_update'),
    path('<int:pk>/delete/', views.item_delete, name='item_delete'),
]