#!/bin/bash
# EduManager — Start server
set -e

cd "$(dirname "$0")"

PORT=${PORT:-8000}

echo "Démarrage EduManager sur le port $PORT..."

# Run migrations automatically
python manage.py migrate --run-syncdb 2>&1 | grep -v "^$" || true

# Collect static files
python manage.py collectstatic --noinput 2>&1 | tail -3 || true

# Create super admin if none exists
python manage.py shell -c "
from apps.users.models import User
if not User.objects.filter(role='super_admin').exists():
    u = User.objects.create_superuser(
        email='admin@edumanager.local',
        password='Admin@2024!',
        first_name='Super',
        last_name='Admin',
        role='super_admin',
    )
    u.must_change_password = False
    u.save()
    print('Super Admin créé: admin@edumanager.local / Admin@2024!')
" 2>&1 || true

exec python manage.py runserver 0.0.0.0:$PORT
