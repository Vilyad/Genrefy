from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Загрузка демо данных из фикстур'

    def handle(self, *args, **kwargs):
        self.stdout.write("Загрузка демо-данных...")

        try:
            call_command('loaddata', 'demo.json', app_label='catalog')
            self.stdout.write(self.style.SUCCESS('Демо-данные успешно загружены!'))

            from catalog.models import Genre, Artist, Track
            self.stdout.write(f"Загружено:")
            self.stdout.write(f"    - Жанров: {Genre.objects.count()}")
            self.stdout.write(f"    - Артистов: {Artist.objects.count()}")
            self.stdout.write(f"    - Треков: {Track.objects.count()}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка загрузки: {str(e)}'))