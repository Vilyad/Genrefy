from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.genre_list, name='genre_list'),
    path('genre/<int:pk>/', views.genre_detail, name='genre_detail'),
]