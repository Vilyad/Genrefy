import os.path

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Экспорт текущих данных в фикстуры'

    def handle(self, *args, **kwargs):
        output_path = 'catalog/fixtures/exported_data.json'

        if os.path.exists(output_path) and not kwargs['force']:
            self.stdout.write(self.style.WARNING(f'Файл {output_path} уже существует.'))

            response = input('Перезаписать? (Y/N): ')
            if response.lower() != 'y':
                self.stdout.write('Отменено.')
                return

        self.stdout.write("Экспорт данных в фикстуры...")

        try:
            os.makedirs('catalog/fixtures', exist_ok=True)

            call_command('dumpdata', 'catalog',
                         indent=2,
                         output='catalog/fixtures/exported_data.json',
                         exclude=['auth', 'contenttypes', 'sessions'])

            file_size = os.path.getsize(output_path)
            self.stdout.write(self.style.SUCCESS('Данные успешно экспортированы!'))
            self.stdout.write(f"Файл: {output_path}")
            self.stdout.write(f"Размер: {file_size / 1024:.1f} KB")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка экспорта: {str(e)}'))