from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.genre_list, name='home'),

    path('genres/', views.genre_list, name='genre_list'),
    path('genres/<int:pk>/', views.genre_detail, name='genre_detail'),
    path('search/', views.search_view, name='search'),
    path('track/<int:pk>/', views.track_detail, name='track_detail'),
    path('track/', views.track_detail, name='track_detail_by_params'),
    path('artist/<int:pk>/', views.artist_detail, name='artist_detail'),
    path('artist/', views.artist_detail, name='artist_detail_by_name'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('save-track/', views.save_track_from_lastfm, name='save_track'),
    path('toggle_favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('add-to-favorites/', views.add_to_favorites, name='add_to_favorites'),
    path('my-favorites/', views.my_favorites, name='my_favorites'),
]
