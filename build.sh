#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py migrate --no-input
python manage.py migrate catalog

python manage.py collectstatic --no-input

echo "=== Creating superuser if not exists ==="
python manage.py shell -c "
from django.contrib.auth.models import User;
import os;
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin');
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com');
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'defaultpassword');
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password);
    print(f'Superuser {username} created');
else:
    print(f'Superuser {username} already exists');
"