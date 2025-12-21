from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Экспорт текущих данных в фикстуры'

    def handle(self, *args, **kwargs):
        self.stdout.write("Экспорт данных в фикстуры...")

        try:
            call_command('dumpdata', 'catalog', indent=2, output='catalog/fixtures/exported_data.json')
            self.stdout.write(self.style.SUCCESS('Данные успешно экспортированы!'))
            self.stdout.write(f"Файл: catalog/fixtures/exported_data.json")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка экспорта: {str(e)}'))