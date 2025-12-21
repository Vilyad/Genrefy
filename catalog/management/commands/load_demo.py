from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
import json

class Command(BaseCommand):
    help = 'Загрузка демо данных из фикстур'

    def handle(self, *args, **kwargs):
        self.stdout.write("Загрузка демо-данных...")

        fixture_path = 'catalog/fixtures/demo.json'

        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f'Файл {fixture_path} не найден!'))
            self.stdout.write(self.style.WARNING('Создаем базовые данные...'))
            self.create_basic_data()
            return

        try:
            call_command('loaddata', 'demo.json', app_label='catalog')
            self.stdout.write(self.style.SUCCESS('Демо-данные успешно загружены!'))

            from catalog.models import Genre, Artist, Track
            self.stdout.write(f"Загружено:")
            self.stdout.write(f"    - Жанров: {Genre.objects.count()}")
            self.stdout.write(f"    - Артистов: {Artist.objects.count()}")
            self.stdout.write(f"    - Треков: {Track.objects.count()}")

        except UnicodeDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Ошибка кодировки файла: {str(e)}'))
            self.stdout.write(self.style.WARNING('Пробуем исправить кодировку...'))
            self.fix_encoding_and_load()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка загрузки: {str(e)}'))
            self.stdout.write(self.style.WARNING('Создаем базовые данные...'))
            self.create_basic_data()

    def fix_encoding_and_load(self):
        try:
            fixture_path = 'catalog/fixtures/demo.json'

            with open(fixture_path, 'rb') as f:
                content_bytes = f.read()

            encodings = ['utf-8-sig', 'cp1251', 'latin-1', 'utf-16']
            decoded_content = None

            for encoding in encodings:
                try:
                    decoded_content = content_bytes.decode(encoding)
                    self.stdout.write(f'успешно декодировано как {encoding}')
                    break
                except UnicodeDecodeError:
                    continue

            if decoded_content:
                with open(fixture_path, 'w', encoding='utf-8') as f:
                    f.write(decoded_content)

                from django.core.management import call_command
                call_command('loaddata', 'demo.json', app_label='catalog')
                self.stdout.write(self.style.SUCCESS('Данные загружены после исправления кодировки!'))
            else:
                raise Exception("Не удалось определить кодировку файла")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Не удалось исправить кодировку: {str(e)}'))
            self.create_basic_data()

    def create_basic_data(self):
        from catalog.models import Genre, Artist, Track

        Track.objects.all().delete()
        Artist.objects.all().delete()
        Genre.objects.all().delete()

        electronic = Genre.objects.create(name="Electronic", description="Электронная музыка")
        rock = Genre.objects.create(name="Rock", description="Рок-музыка")
        hiphop = Genre.objects.create(name="Hip Hop", description="Хип-хоп и рэп")
        pop = Genre.objects.create(name="Pop", description="Поп-музыка")
        jazz = Genre.objects.create(name="Jazz", description="Джаз")

        daft_punk = Artist.objects.create(name="Daft Punk", spotify_id="demo_1")
        daft_punk.genres.add(electronic)

        beatles = Artist.objects.create(name="The Beatles", spotify_id="demo_2")
        beatles.genres.add(rock)

        kendrick = Artist.objects.create(name="Kendrick Lamar", spotify_id="demo_3")
        kendrick.genres.add(hiphop)

        taylor = Artist.objects.create(name="Taylor Swift", spotify_id="demo_4")
        taylor.genres.add(pop)

        miles = Artist.objects.create(name="Miles Davis", spotify_id="demo_5")
        miles.genres.add(jazz)

        Track.objects.create(
            title="Get Lucky",
            artist=daft_punk,
            spotify_id="demo_track_1",
            audio_features={"danceability": 0.7, "energy": 0.8, "valence": 0.9},
        )

        Track.objects.create(
            title="Hey Jude",
            artist=beatles,
            spotify_id="demo_track_2",
            audio_features={"danceability": 0.5, "energy": 0.4, "valence": 0.6},
        )

        self.stdout.write(self.style.SUCCESS('Базовые демо-данные созданы!'))