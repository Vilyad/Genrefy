"""
Скрипт для запуска тестов.
"""
import os
import sys
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY='test-secret-key-for-tests',
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'catalog',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        LASTFM_API_KEY='test_api_key',
        LASTFM_SHARED_SECRET='test_shared_secret',
        CACHE_TTL_DAYS=7,
        CACHE_DIR='.cache_test',
        USE_TZ=True,
    )

django.setup()


def run_tests():
    """Запуск всех тестов."""
    import unittest

    loader = unittest.TestLoader()

    service_tests = loader.discover(
        start_dir='catalog/tests/services',
        pattern='test_*.py'
    )

    suite = unittest.TestSuite()
    suite.addTests(service_tests)

    runner = unittest.TextTestRunner(
        verbosity=2,
        failfast=False,
        buffer=False
    )

    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    sys.exit(run_tests())
