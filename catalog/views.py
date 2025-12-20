from django.shortcuts import render, get_object_or_404
from .models import Genre, Artist, Track


def genre_list(request):
    genres = Genre.objects.all()

    for genre in genres:
        track_count = Track.objects.filter(artist__genres=genre).count()
        genre.track_count = track_count

        artist_count = Artist.objects.filter(genres=genre).count()
        genre.artist_count = artist_count

    return render(request, 'catalog/genre_list.html', {
        'genres': genres,
        'page_title': 'Каталог музыкальных жанров'
    })


def genre_detail(request, pk):
    genre = get_object_or_404(Genre, pk=pk)

    artists = Artist.objects.filter(genres=genre)

    tracks = Track.objects.filter(artist__genres=genre).select_related('artist')

    return render(request, 'catalog/genre_detail.html', {
        'genre': genre,
        'artists': artists[:10],
        'tracks': tracks[:20],
        'page_title': f'Жанр: {genre.name}'
    })