from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Genre, Artist, Track
from .forms import SearchForm, AddTrackFromLastFMForm, FavoriteForm, GenreAnalysisForm
from .services import CatalogService, AnalyticsService


def genre_list(request):
    """Список жанров."""
    genres = CatalogService.get_genre_statistics()
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

        favorite_form = FavoriteForm(initial={
            'track_id': track.id,
            'track_name': track.title,
            'artist_id': track.artist.id,
            'artist_name': track.artist.name
        })

        return render(request, 'catalog/track_detail.html', {
            'track': track,
            'tags': track.tags[:10],
            'favorite_form': favorite_form,
            'page_title': f'{track.title} - {track.artist.name}'
        })

    elif request.GET.get('artist') and request.GET.get('track'):
        track_name = request.GET.get('track')
        artist_name = request.GET.get('artist')

        track, created = CatalogService.get_or_create_track_from_lastfm(track_name, artist_name)

        if track:
            return redirect('track_detail', pk=track.pk)
        else:
            messages.error(request, 'Трек не найден')
            return redirect('search')

    messages.error(request, 'Не указаны параметры')
    return redirect('search')


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

            return redirect('track_detail', pk=track.id)

    return redirect('genre_list')


@login_required
def my_favorites(request):
    """Избранное пользователя."""
    data = CatalogService.get_user_favorites_with_recommendations(request.user)

    return render(request, 'catalog/favorites.html', {
        **data,
        'page_title': 'Мои избранные жанры'
    })


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

                return redirect('track_detail', pk=track.pk)
            else:
                messages.error(request, 'Не удалось сохранить трек')

    else:
        form = AddTrackFromLastFMForm()

    return render(request, 'catalog/save_track.html', {
        'form': form,
        'page_title': 'Сохранить трек'
    })
