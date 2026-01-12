import json

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import SearchForm, AddTrackFromLastFMForm, FavoriteForm, GenreAnalysisForm, RegistrationForm
from .models import Genre, Artist, Track, Favorite
from .services import CatalogService, AnalyticsService


class CustomLoginView(LoginView):
    template_name = 'catalog/login.html'
    redirect_authenticated_user = True
    next_page = reverse_lazy('catalog:genre_list')

    def form_invalid(self, form):
        messages.error(self.request, 'Неверное имя пользователя или пароль. Попробуйте еще раз.')
        return super().form_invalid(form)


def register(request):
    """Регистрация нового пользователя."""
    if request.user.is_authenticated:
        return redirect('catalog:genre_list')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! Регистрация успешна.')
            return redirect('catalog:genre_list')
    else:
        form = RegistrationForm()

    return render(request, 'catalog/register.html', {
        'form': form,
        'page_title': 'Регистрация'
    })


def logout_view(request):
    """Выход пользователя."""
    auth_logout(request)
    return redirect('catalog:genre_list')


@login_required
def profile(request):
    """Страница профиля пользователя."""
    return render(request, 'catalog/profile.html', {
        'page_title': f'Профиль {request.user.username}'
    })


@csrf_exempt
@require_POST
@login_required
def toggle_favorite(request):
    """Добавление/удаление элемента из избранного (AJAX)."""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        item_type = data.get('item_type', 'genre')

        if not item_id:
            return JsonResponse({'status': 'error', 'message': 'No item_id provided'})

        if item_type == 'genre':
            try:
                genre = Genre.objects.get(id=item_id)
                item_id = str(genre.id)
            except (Genre.DoesNotExist, ValueError):
                return JsonResponse({'status': 'error', 'message': 'Genre not found'})

        favorite = Favorite.objects.filter(
            user=request.user,
            item_type=item_type,
            item_id=item_id
        ).first()

        if favorite:
            favorite.delete()
            action = 'removed'
            is_favorite = False
        else:
            Favorite.objects.create(
                user=request.user,
                item_type=item_type,
                item_id=item_id
            )
            action = 'added'
            is_favorite = True

        return JsonResponse({
            'status': 'success',
            'action': action,
            'is_favorite': is_favorite,
            'item_id': item_id,
            'item_type': item_type
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def genre_list(request):
    """Список жанров с поиском и фильтрацией."""
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort', 'popularity')
    favorites_only = request.GET.get('favorites', 'false') == 'true'

    genres = CatalogService.get_genre_statistics(limit=100)

    favorite_genres_ids = []
    if request.user.is_authenticated:
        favorite_genres_ids = Favorite.objects.filter(
            user=request.user,
            item_type='genre'
        ).values_list('item_id', flat=True)

    if favorites_only and request.user.is_authenticated:
        genres = [genre for genre in genres if str(genre.id) in favorite_genres_ids]

    if search_query:
        genres = [genre for genre in genres
                  if search_query.lower() in genre.name.lower()]

    try:
        if sort_by == 'name':
            genres = sorted(genres, key=lambda x: x.name.lower() if x.name else '')
        elif sort_by == 'tracks':
            genres = sorted(genres,
                            key=lambda x: getattr(x, 'display_track_count', 0) or 0,
                            reverse=True)
        else:
            genres = sorted(genres,
                            key=lambda x: getattr(x, 'total_playcount', 0) or 0,
                            reverse=True)
    except TypeError as e:
        print(f"Sorting error: {e}")
        genres = sorted(genres, key=lambda x: x.name.lower() if x.name else '')

    for genre in genres:
        genre.display_track_count = getattr(genre, 'annotated_track_count', 0) or 0
        genre.display_artist_count = getattr(genre, 'annotated_artist_count', 0) or 0
        genre.total_playcount = getattr(genre, 'total_playcount', 0) or 0
        genre.is_favorite = str(genre.id) in favorite_genres_ids

    total_favorites = len(favorite_genres_ids) if request.user.is_authenticated else 0
    showing_favorites = favorites_only and request.user.is_authenticated

    return render(request, 'catalog/genre_list.html', {
        'genres': genres,
        'search_query': search_query,
        'sort_by': sort_by,
        'favorites_only': favorites_only,
        'genres_count': len(genres),
        'total_favorites': total_favorites,
        'showing_favorites': showing_favorites,
        'user_authenticated': request.user.is_authenticated,
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
            'favorite_form': favorite_form,
            'page_title': f'{track.title} - {track.artist.name}'
        })

    elif request.GET.get('artist') and request.GET.get('track'):
        track_name = request.GET.get('track')
        artist_name = request.GET.get('artist')

        track = Track.objects.filter(
            title__iexact=track_name,
            artist__name__iexact=artist_name
        ).first()

        if track:
            return redirect('catalog:track_detail', pk=track.pk)
        else:
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

        artist = Artist.objects.filter(name__iexact=artist_name).first()

        if artist:
            return redirect('catalog:artist_detail', pk=artist.pk)
        else:
            artist, created = CatalogService.get_or_create_artist_from_lastfm(artist_name)

            if artist:
                return redirect('catalog:artist_detail', pk=artist.pk)
            else:
                messages.error(request, f'Исполнитель "{artist_name}" не найден в Last.fm')
                return redirect('catalog:search')

    messages.error(request, 'Не указано имя исполнителя')
    return redirect('catalog:search')


def analytics_view(request):
    """Аналитика жанров."""
    form = GenreAnalysisForm(request.GET or None)

    if form.is_valid():
        time_period = form.cleaned_data.get('time_period', 'overall')
        limit = form.cleaned_data.get('limit', 10)
    else:
        time_period = 'overall'
        limit = 10

    data = AnalyticsService.get_analytics_data(limit)

    return render(request, 'catalog/analytics.html', {
        'form': form,
        **data,
        'page_title': 'Аналитика музыкальных жанров'
    })


@login_required
def add_to_favorites(request):
    """Добавление в избранное (через форму на странице трека)."""
    if request.method == 'POST':
        form = FavoriteForm(request.POST)
        if form.is_valid():
            track_id = form.cleaned_data['track_id']
            track = get_object_or_404(Track, id=track_id)

            added, existing = CatalogService.add_to_favorites(request.user, track)

            if added > 0:
                messages.success(request, f'Добавлено {added} жанров в избранное')
            elif existing > 0:
                messages.info(request, 'Эти жанры уже в избранном')
            else:
                messages.warning(request, 'У трека нет жанров для добавления')

            return redirect('catalog:track_detail', pk=track.id)

    return redirect('catalog:genre_list')


@login_required
def my_favorites(request):
    """Избранное пользователя."""
    favorite_genres_ids = Favorite.objects.filter(
        user=request.user,
        item_type='genre'
    ).values_list('item_id', flat=True)

    genre_ids = []
    for item_id in favorite_genres_ids:
        try:
            genre_ids.append(int(item_id))
        except (ValueError, TypeError):
            continue

    if not genre_ids:
        favorite_genres = Genre.objects.none()
    else:
        favorite_genres = Genre.objects.filter(id__in=genre_ids)

    recommendations = {
        'artists': Artist.objects.filter(genres__in=favorite_genres).distinct()[:4],
        'tracks': Track.objects.filter(artist__genres__in=favorite_genres).distinct()[:5]
    }

    return render(request, 'catalog/favorites.html', {
        'favorite_genres': favorite_genres,
        'recommendations': recommendations,
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
