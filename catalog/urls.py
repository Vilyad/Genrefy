from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.genre_list, name='home'),

    path('genres/', views.genre_list, name='genre_list'),
    path('genres/<int:pk>/', views.genre_detail, name='genre_detail'),

    path('search/', views.search_view, name='search'),

    path('tracks/', views.track_detail, name='track_detail'),
    path('tracks/<int:pk>/', views.track_detail, name='track_detail_pk'),

    path('artists/', views.artist_detail, name='artist_detail'),
    path('artists/<int:pk>/', views.artist_detail, name='artist_detail_pk'),

    path('analytics/', views.analytics_view, name='analytics'),

    path('favorites/add/', views.add_to_favorites, name='add_to_favorites'),
    path('my-favorites/', views.my_favorites, name='my_favorites'),

    path('save-track/', views.save_track_from_lastfm, name='save_track'),
]
