from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from .forms import SearchForm, AddTrackFromLastFMForm, FavoriteForm, GenreAnalysisForm
from .models import Artist, Track
from .services import CatalogService, AnalyticsService


def genre_list(request):
    """Список жанров."""
    genres = CatalogService.get_genre_statistics()

    for genre in genres:
        genre.display_track_count = genre.annotated_track_count or 0
        genre.display_artist_count = genre.annotated_artist_count or 0

    return render(request, 'catalog/genre_list.html', {
        'genres': genres,
        'page_title': 'Каталог музыкальных жанров'
    })


def genre_detail(request, pk):
    """Детальная страница жанра."""
    genre, artists, tracks, top_tracks = CatalogService.get_genre_with_details(pk)

    return render(request, 'catalog/genre_detail.html', {
        'genre': genre,
        'artists': artists,
        'tracks': tracks,
        'top_tracks': top_tracks,
        'page_title': f'Жанр: {genre.name}'
    })


def search_view(request):
    """Поиск в Last.fm."""
    form = SearchForm(request.GET or None)
    results = []

    if form.is_valid():
        query = form.cleaned_data['query']
        search_type = form.cleaned_data['search_type']
        results = CatalogService.search_in_lastfm(query, search_type)

    return render(request, 'catalog/search_results.html', {
        'form': form,
        'results': results,
        'search_type': form.cleaned_data.get('search_type', 'track') if form.is_bound else 'track',
        'page_title': 'Поиск музыки'
    })


def track_detail(request, pk=None):
    """Детальная страница трека."""
    if pk:
        track = get_object_or_404(Track, pk=pk)

        if not track.get_lastfm_data():
            CatalogService.update_track_from_lastfm(track)
            track.refresh_from_db()

        favorite_form = FavoriteForm(initial={
            'track_id': track.id,
            'track_name': track.title,
            'artist_id': track.artist.id,
            'artist_name': track.artist.name
        })

        return render(request, 'catalog/track_detail.html', {
            'track': track,
            'tags': track.tags[:10] if track.tags else [],
            'favorite_form': favorite_form,
            'page_title': f'{track.title} - {track.artist.name}'
        })

    elif request.GET.get('artist') and request.GET.get('track'):
        track_name = request.GET.get('track')
        artist_name = request.GET.get('artist')

        track, created = CatalogService.get_or_create_track_from_lastfm(track_name, artist_name)

        if track:
            return redirect('catalog:track_detail', pk=track.pk)
        else:
            messages.error(request, 'Трек не найден')
            return redirect('catalog:search')

    messages.error(request, 'Не указаны параметры')
    return redirect('catalog:search')


def artist_detail(request, pk=None):
    """Детальная страница исполнителя."""
    if pk:
        artist = get_object_or_404(Artist, pk=pk)

        top_tracks = artist.tracks.order_by('-lastfm_playcount')[:10]
        genres = artist.genres.all()

        return render(request, 'catalog/artist_detail.html', {
            'artist': artist,
            'top_tracks': top_tracks,
            'genres': genres,
            'page_title': f'Исполнитель: {artist.name}'
        })

    elif request.GET.get('artist'):
        artist_name = request.GET.get('artist')

        artist, created = CatalogService.get_or_create_artist_from_lastfm(artist_name)

        if artist:
            return redirect('catalog:artist_detail_pk', pk=artist.pk)
        else:
            messages.error(request, 'Исполнитель не найден в Last.fm')
            return redirect('catalog:search')

    messages.error(request, 'Не указано имя исполнителя')
    return redirect('catalog:search')


def analytics_view(request):
    """Аналитика жанров."""
    form = GenreAnalysisForm(request.GET or None)

    time_period = form.cleaned_data.get('time_period', 'overall') if form.is_valid() else 'overall'
    limit = form.cleaned_data.get('limit', 10) if form.is_valid() else 10

    data = AnalyticsService.get_analytics_data(time_period, limit)

    return render(request, 'catalog/analytics.html', {
        'form': form,
        **data,
        'page_title': 'Аналитика музыкальных жанров'
    })


@login_required
def add_to_favorites(request):
    """Добавление в избранное."""
    if request.method == 'POST':
        form = FavoriteForm(request.POST)
        if form.is_valid():
            track_id = form.cleaned_data['track_id']
            track = get_object_or_404(Track, id=track_id)

            added, existing = CatalogService.add_to_favorites(request.user, track)

            if added > 0:
                messages.success(request, f'Добавлено {added} жанров в избранное')
            else:
                messages.info(request, 'Эти жанры уже в избранном')

            return redirect('catalog:track_detail', pk=track.id)

    return redirect('catalog:genre_list')


@login_required
def my_favorites(request):
    """Избранное пользователя."""
    data = CatalogService.get_user_favorites_with_recommendations(request.user)

    return render(request, 'catalog/favorites.html', {
        **data,
        'page_title': 'Мои избранные жанры'
    })


def save_track_from_lastfm(request):
    """Сохранение трека из Last.fm."""
    if request.method == 'POST':
        form = AddTrackFromLastFMForm(request.POST)
        if form.is_valid():
            track_name = form.cleaned_data['track_name']
            artist_name = form.cleaned_data['artist_name']

            track, created = CatalogService.get_or_create_track_from_lastfm(track_name, artist_name)

            if track:
                if created:
                    messages.success(request, f'Трек "{track_name}" сохранен!')
                else:
                    messages.info(request, f'Трек "{track_name}" уже есть')

                return redirect('catalog:track_detail', pk=track.pk)
            else:
                messages.error(request, 'Не удалось сохранить трек')

    else:
        initial_data = {}
        if request.GET.get('track_name'):
            initial_data['track_name'] = request.GET.get('track_name')
        if request.GET.get('artist_name'):
            initial_data['artist_name'] = request.GET.get('artist_name')

        form = AddTrackFromLastFMForm(initial=initial_data)

    return render(request, 'catalog/save_track.html', {
        'form': form,
        'page_title': 'Сохранить трек из Last.fm'
    })
