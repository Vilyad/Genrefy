from django.core.management.base import BaseCommand
from catalog.models import Genre, Artist, Track
import json
from pathlib import Path

class Command(BaseCommand):
    help = 'Загрузка демо-данных для тестирования'

    def handle(self, *args, **kwargs):
        genres_data = [
            {'name' : 'Electronic', 'description': 'Электронная музыка'},
            {'name': 'Rock', 'description': 'Рок-музыка'},
            {'name': 'Hip Hop', 'description': 'Хип-хоп и рэп'},
            {'name': 'Pop', 'description': 'Поп-музыка'},
            {'name': 'Jazz', 'description': 'Джаз'},
        ]

        for genre_data in genres_data:
            Genre.objects.get_or_create(**genre_data)

        artists_data = [
            {'name': 'Daft Punk', 'spotify_id': 'spotify:artist:4tZwfgrHOc3mvqYlEYSvVi'},
            {'name': 'The Beatles', 'spotify_id': 'spotify:artist:3WrFJ7ztbogyGnTHbHJFl2'},
            {'name': 'Kendrick Lamar', 'spotify_id': 'spotify:artist:2YZyLoL8N0Wb9xBt1NhZWg'},
            {'name': 'Taylor Swift', 'spotify_id': 'spotify:artist:06HL4z0CvFAxyc27GXpf02'},
            {'name': 'Miles Davis', 'spotify_id': 'spotify:artist:0kbYTNQb4Pb1rPbbaF0pT4'},
        ]

        for artist_data in artists_data:
            Artist.objects.get_or_create(**artist_data)

        electronic = Genre.objects.get(name='Electronic')
        rock = Genre.objects.get(name='Rock')
        hiphop = Genre.objects.get(name='Hip Hop')
        pop = Genre.objects.get(name='Pop')
        jazz = Genre.objects.get(name='Jazz')

        daft_punk = Artist.objects.get(name='Daft Punk')
        beatles = Artist.objects.get(name='The Beatles')
        kendrick = Artist.objects.get(name='Kendrick Lamar')
        taylor = Artist.objects.get(name='Taylor Swift')
        miles = Artist.objects.get(name='Miles Davis')

        daft_punk.genres.add(electronic)
        beatles.genres.add(rock)
        kendrick.genres.add(hiphop)
        taylor.genres.add(pop)
        miles.genres.add(jazz)

        tracks_data = [
            {
                'title': 'Get Lucky',
                'artist': daft_punk,
                'spotify_id': 'spotify:track:69kOkLUCkxIZYexIgSG8rq',
                'audio_features': {
                    'danceability': 0.766,
                    'energy': 0.674,
                    'valence': 0.966,
                    'tempo': 116.0,
                    'acousticness': 0.0102,
                    'instrumentalness': 0.0214,
                }
            },
            {
                'title': 'Hey Jude',
                'artist': beatles,
                'spotify_id': 'spotify:track:0aym2LBJBk9DAYuHHutrIl',
                'audio_features': {
                    'danceability': 0.545,
                    'energy': 0.445,
                    'valence': 0.634,
                    'tempo': 145.2,
                    'acousticness': 0.565,
                    'instrumentalness': 0.0012,
                }
            },
        ]

        for track_data in tracks_data:
            Track.objects.get_or_create(**track_data)

        self.stdout.write(self.style.SUCCESS('Демо-данные успешно загружены!'))