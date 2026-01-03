"""
Команда для загрузки демо-данных.
"""
import json
from django.core.management.base import BaseCommand
from catalog.models import Genre, Artist, Track
from catalog.services import LastFMService


class Command(BaseCommand):
    """Команда для загрузки демо-данных."""

    help = 'Загружает демо-данные для тестирования приложения'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед загрузкой'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Количество треков для загрузки (по умолчанию: 10)'
        )

    def handle(self, *args, **options):
        clear_data = options['clear']
        track_count = options['count']

        if clear_data:
            self.stdout.write("Очистка существующих данных...")
            Track.objects.all().delete()
            Artist.objects.all().delete()
            Genre.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Данные очищены"))

        self.stdout.write(f"Загрузка демо-данных ({track_count} треков)...")

        genres_data = [
            {'name': 'Rock', 'lastfm_tag': 'rock', 'description': 'Рок-музыка'},
            {'name': 'Pop', 'lastfm_tag': 'pop', 'description': 'Популярная музыка'},
            {'name': 'Hip Hop', 'lastfm_tag': 'hip hop', 'description': 'Хип-хоп и рэп'},
            {'name': 'Electronic', 'lastfm_tag': 'electronic', 'description': 'Электронная музыка'},
            {'name': 'Jazz', 'lastfm_tag': 'jazz', 'description': 'Джазовая музыка'},
            {'name': 'Classical', 'lastfm_tag': 'classical', 'description': 'Классическая музыка'},
            {'name': 'Alternative', 'lastfm_tag': 'alternative', 'description': 'Альтернативная музыка'},
            {'name': 'Indie', 'lastfm_tag': 'indie', 'description': 'Инди-музыка'},
        ]

        genres = {}
        for genre_data in genres_data:
            genre, created = Genre.objects.get_or_create(
                name=genre_data['name'],
                defaults=genre_data
            )
            genres[genre.name.lower()] = genre
            if created:
                self.stdout.write(f"Создан жанр: {genre.name}")

        popular_tracks = [
            {'artist': 'Queen', 'track': 'Bohemian Rhapsody'},
            {'artist': 'The Beatles', 'track': 'Yesterday'},
            {'artist': 'Led Zeppelin', 'track': 'Stairway to Heaven'},
            {'artist': 'Michael Jackson', 'track': 'Billie Jean'},
            {'artist': 'Madonna', 'track': 'Like a Prayer'},
            {'artist': 'Nirvana', 'track': 'Smells Like Teen Spirit'},
            {'artist': 'Radiohead', 'track': 'Creep'},
            {'artist': 'Coldplay', 'track': 'Yellow'},
            {'artist': 'Adele', 'track': 'Hello'},
            {'artist': 'Ed Sheeran', 'track': 'Shape of You'},
            {'artist': 'Daft Punk', 'track': 'Around the World'},
            {'artist': 'Kraftwerk', 'track': 'The Model'},
            {'artist': 'OutKast', 'track': 'Hey Ya!'},
            {'artist': 'Eminem', 'track': 'Lose Yourself'},
            {'artist': 'Miles Davis', 'track': 'So What'},
            {'artist': 'John Coltrane', 'track': 'Giant Steps'},
        ]

        tracks_to_load = popular_tracks[:track_count]

        lastfm_service = LastFMService()

        for i, demo_track in enumerate(tracks_to_load, 1):
            try:
                self.stdout.write(
                    f"[{i}/{len(tracks_to_load)}] Поиск: {demo_track['artist']} - {demo_track['track']}")

                track_info = lastfm_service.get_track_info(
                    artist=demo_track['artist'],
                    track=demo_track['track']
                )

                if not track_info:
                    self.stdout.write(self.style.WARNING(f"Не найден: {demo_track['track']}"))
                    continue

                artist_obj, artist_created = Artist.objects.get_or_create(
                    name=track_info['artist'],
                    defaults={
                        'lastfm_url': track_info.get('url', ''),
                        'lastfm_listeners': track_info.get('listeners', 0),
                        'lastfm_playcount': track_info.get('playcount', 0),
                        'image_url': track_info.get('image', ''),
                        'description': f'Демо-артист: {track_info["artist"]}'
                    }
                )

                if not artist_created:
                    artist_obj.lastfm_listeners = track_info.get('listeners', 0)
                    artist_obj.lastfm_playcount = track_info.get('playcount', 0)
                    if track_info.get('image'):
                        artist_obj.image_url = track_info['image']
                    artist_obj.save()

                track_obj, track_created = Track.objects.get_or_create(
                    title=track_info['name'],
                    artist=artist_obj,
                    defaults={
                        'lastfm_url': track_info.get('url', ''),
                        'lastfm_listeners': track_info.get('listeners', 0),
                        'lastfm_playcount': track_info.get('playcount', 0),
                        'duration': track_info.get('duration'),
                        'album': track_info.get('album', ''),
                        'tags': track_info.get('tags', []),
                        'image_url': track_info.get('image', ''),
                        'is_reference': True,
                    }
                )

                track_obj.set_lastfm_data(track_info)

                if track_created and track_info.get('tags'):
                    track_obj.link_genres_from_tags()

                if track_created:
                    self.stdout.write(self.style.SUCCESS(
                        f"Добавлен: {track_obj.title} - {artist_obj.name}"
                    ))
                else:
                    self.stdout.write(self.style.NOTICE(
                        f"Уже существует: {track_obj.title}"
                    ))

                import time
                time.sleep(0.3)

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Ошибка при добавлении {demo_track['track']}: {str(e)}"
                ))

        self.stdout.write("Обновление статистики жанров...")
        for genre in Genre.objects.all():
            genre.track_count = Track.objects.filter(
                tags_json__icontains=genre.name.lower()
            ).count()
            genre.is_popular = genre.track_count > 5
            genre.save()

        self.stdout.write(self.style.SUCCESS("Демо-данные успешно загружены!"))

        self.stdout.write("\nСтатистика:")
        self.stdout.write(f"  Жанров: {Genre.objects.count()}")
        self.stdout.write(f"  Артистов: {Artist.objects.count()}")
        self.stdout.write(f"  Треков: {Track.objects.count()}")

        self.stdout.write("\n🏆 Топ 5 треков по прослушиваниям:")
        for track in Track.objects.order_by('-lastfm_playcount')[:5]:
            self.stdout.write(
                f"  • {track.title} - {track.artist.name} "
                f"({track.lastfm_playcount:,} прослушиваний)"
            )
