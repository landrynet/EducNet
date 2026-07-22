#!/bin/bash
# EduManager — First-time setup script
set -e

cd "$(dirname "$0")"

echo "═══════════════════════════════════════════════"
echo "  EduManager — Configuration initiale"
echo "═══════════════════════════════════════════════"

# Run migrations
echo "[1/4] Création des tables de base de données..."
python manage.py migrate --run-syncdb 2>&1 | tail -20

# Collect static files
echo "[2/4] Collecte des fichiers statiques..."
python manage.py collectstatic --noinput 2>&1 | tail -5

# Create Super Admin
echo "[3/4] Création du Super Administrateur..."
python manage.py shell -c "
from apps.users.models import User
if not User.objects.filter(email='admin@edumanager.local').exists():
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
else:
    print('Super Admin existe déjà.')
" 2>&1

echo "[4/4] Configuration terminée !"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Identifiants Super Admin:"
echo "  Email:         admin@edumanager.local"
echo "  Mot de passe:  Admin@2024!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
