#!/bin/bash

# EduManager — Script de démarrage V1.3
# ─────────────────────────────────────────────────────────────
# Ce script :
#   1. Crée ou active l'environnement virtuel Python (.venv)
#   2. Installe / met à jour les dépendances
#   3. Applique les migrations de base de données
#   4. Collecte les fichiers statiques
#   5. Crée le Super Admin s'il n'existe pas
#   6. Charge les données de test
#   7. Démarre le serveur Django
# ─────────────────────────────────────────────────────────────

set -e

# ── Se placer dans le dossier du projet ───────────────────────

cd "$(dirname "$0")"

# ── Mise à jour depuis GitHub ─────────────────────────────────

if git remote get-url origin &>/dev/null; then
    echo -e "\033[0;34m[EduManager]\033[0m Récupération des mises à jour (git pull origin main)..."
    git pull origin main || echo -e "\033[1;33m[!]\033[0m git pull a échoué (réseau indisponible ?). Démarrage avec la version locale."
fi

# ── Configuration ─────────────────────────────────────────────

PORT=${PORT:-8000}
VENV_DIR=".venv"
REQ_FILE="requirements.txt"
REQ_HASH_FILE="$VENV_DIR/.req_hash"

# ── Couleurs ──────────────────────────────────────────────────

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'

log() {
    echo -e "${BLUE}[EduManager]${RESET} $1"
}

ok() {
    echo -e "${GREEN}[✓]${RESET} $1"
}

warn() {
    echo -e "${YELLOW}[!]${RESET} $1"
}

error() {
    echo -e "${RED}[✗]${RESET} $1"
}

# ── En-tête ───────────────────────────────────────────────────

echo ""
echo -e "${BLUE}══════════════════════════════════════════════${RESET}"
echo -e "${BLUE}  EduManager V1.3 — Port $PORT${RESET}"
echo -e "${BLUE}══════════════════════════════════════════════${RESET}"
echo ""

# ── Vérification de Python ────────────────────────────────────

if ! command -v python &>/dev/null; then
    error "Python n'est pas installé ou n'est pas accessible dans le PATH."
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1)

log "Python détecté : $PYTHON_VERSION"

# ── Vérification de requirements.txt ──────────────────────────

if [ ! -f "$REQ_FILE" ]; then
    error "$REQ_FILE introuvable."
    exit 1
fi

# ── 1. Environnement virtuel ──────────────────────────────────

if [ ! -d "$VENV_DIR" ]; then

    log "Création de l'environnement virtuel (.venv)..."

    python -m venv "$VENV_DIR" --system-site-packages

    ok "Environnement virtuel créé."

else

    ok "Environnement virtuel existant (.venv)."

fi

# ── Activation compatible Windows / Linux / macOS ─────────────

if [ -f "$VENV_DIR/Scripts/activate" ]; then

    # Windows avec Git Bash
    source "$VENV_DIR/Scripts/activate"

elif [ -f "$VENV_DIR/bin/activate" ]; then

    # Linux / macOS
    source "$VENV_DIR/bin/activate"

else

    error "Script d'activation de l'environnement virtuel introuvable."

    echo ""
    echo "Vérifie le contenu du dossier .venv avec :"
    echo "ls -la .venv"

    exit 1

fi

# Neutraliser PIP_USER
export PIP_USER=0

ok "Environnement virtuel activé."

# ── Vérification du Python utilisé ────────────────────────────

log "Python utilisé : $(python --version 2>&1)"
log "Pip utilisé : $(python -m pip --version)"

# ── 2. Dépendances ─────────────────────────────────────────────

CURRENT_HASH=""
SAVED_HASH=""

# Calcul du hash du fichier requirements.txt

if command -v md5sum &>/dev/null; then

    CURRENT_HASH=$(md5sum "$REQ_FILE" 2>/dev/null | awk '{print $1}')

elif command -v md5 &>/dev/null; then

    CURRENT_HASH=$(md5 -q "$REQ_FILE" 2>/dev/null)

fi

# Lecture de l'ancien hash

if [ -f "$REQ_HASH_FILE" ]; then

    SAVED_HASH=$(cat "$REQ_HASH_FILE")

fi

# Installation si requirements.txt a changé

if [ "$CURRENT_HASH" != "$SAVED_HASH" ] || [ -z "$CURRENT_HASH" ]; then

    log "Installation des dépendances depuis $REQ_FILE..."

    # Mise à jour de pip sans utiliser le cache
    python -m pip install --upgrade pip \
        --quiet \
        --disable-pip-version-check \
        --no-cache-dir

    # Installation propre des dépendances
    python -m pip install -r "$REQ_FILE" \
        --quiet \
        --disable-pip-version-check \
        --no-cache-dir

    # Sauvegarde du hash
    if [ -n "$CURRENT_HASH" ]; then

        echo "$CURRENT_HASH" > "$REQ_HASH_FILE"

    fi

    ok "Dépendances installées / mises à jour."

else

    ok "Dépendances déjà à jour."

fi

# ── 3. Vérification Django ────────────────────────────────────

log "Vérification de la configuration Django..."

python manage.py check

ok "Configuration Django valide."

# ── 4. Migrations ─────────────────────────────────────────────

log "Application des migrations..."

MIGRATION_LOG="${TMPDIR:-/tmp}/edumanager-migrate-${RANDOM}.log"

if python manage.py migrate --run-syncdb --fake-initial >"$MIGRATION_LOG" 2>&1; then

    cat "$MIGRATION_LOG"
    rm -f "$MIGRATION_LOG"

else

    cat "$MIGRATION_LOG"

    warn "La migration standard a échoué. Vérification d'une ancienne base avec tables timetable existantes..."

    if ! grep -Fq 'table "timetable_timeslot" already exists' "$MIGRATION_LOG"; then
        error "La migration a échoué pour une raison différente. Aucune réparation automatique effectuée."
        rm -f "$MIGRATION_LOG"
        exit 1
    fi

    rm -f "$MIGRATION_LOG"

    # Certaines anciennes installations ont créé une partie des tables du
    # module timetable avant l'ajout de ses migrations. On complète uniquement
    # les tables absentes : les tables et les données existantes sont conservées.
    # Une copie de sauvegarde est créée avant toute modification du schéma.
    python manage.py shell -c "
from django.conf import settings
from django.db import connection
from pathlib import Path
from shutil import copy2
from datetime import datetime

from apps.timetable.models import TimeSlot, TimetableSchedule, TimetableEntry

database = Path(settings.DATABASES['default']['NAME'])
if database.exists():
    backup = database.with_name(
        database.name + '.before-timetable-repair-' +
        datetime.now().strftime('%Y%m%d-%H%M%S') + '.bak'
    )
    copy2(database, backup)
    print('Sauvegarde créée : ' + str(backup))

models = [TimeSlot, TimetableSchedule, TimetableEntry]
with connection.cursor() as cursor:
    existing = set(connection.introspection.table_names(cursor))

missing = [model for model in models if model._meta.db_table not in existing]
if missing:
    print('Création des tables timetable manquantes : ' +
          ', '.join(model._meta.db_table for model in missing))
    with connection.schema_editor() as schema_editor:
        for model in missing:
            schema_editor.create_model(model)
else:
    print('Tables timetable déjà présentes, aucune création nécessaire.')
"

    warn "Schéma timetable réparé sans suppression de données. Marquage de timetable.0001 comme appliquée..."
    python manage.py migrate timetable 0001 --fake

    if python manage.py shell -c "
from django.db import connection
import sys

with connection.cursor() as cursor:
    tables = set(connection.introspection.table_names(cursor))
sys.exit(0 if 'timetable_schoolconfig' in tables else 1)
"; then
        warn "Table timetable_schoolconfig détectée. Marquage de timetable.0002 comme appliquée..."
        python manage.py migrate timetable 0002 --fake
    fi

    python manage.py migrate --run-syncdb --fake-initial

fi

ok "Migrations terminées."

# ── 4b. Tables M2M non-migrées (created by syncdb only on fresh DB) ──────────

python manage.py shell -c "
from django.db import connection
tables_needed = [
    ('academic_classroom_subjects',
     '''CREATE TABLE IF NOT EXISTS academic_classroom_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        classroom_id INTEGER NOT NULL REFERENCES academic_classroom(id) DEFERRABLE INITIALLY DEFERRED,
        subject_id   INTEGER NOT NULL REFERENCES academic_subject(id)  DEFERRABLE INITIALLY DEFERRED,
        UNIQUE(classroom_id, subject_id)
     )'''),
]
with connection.cursor() as c:
    for table_name, ddl in tables_needed:
        c.execute(ddl)
"

# ── 5. Fichiers statiques ─────────────────────────────────────

log "Collecte des fichiers statiques..."

python manage.py collectstatic --noinput

ok "Fichiers statiques collectés."

# ── 6. Super Admin ────────────────────────────────────────────

log "Vérification du Super Admin..."

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

    print('Super Admin créé.')

else:

    print('Super Admin déjà présent.')
"

ok "Super Admin vérifié."

# ── 7. Données de test ────────────────────────────────────────

if [ -f "seed_test_data.py" ]; then

    log "Chargement des données de test..."

    python seed_test_data.py

    ok "Données de test traitées."

else

    warn "seed_test_data.py introuvable. Étape ignorée."

fi

# ── 8. Démarrage du serveur ──────────────────────────────────

echo ""

echo -e "${GREEN}══════════════════════════════════════════════${RESET}"
echo -e "${GREEN}  Serveur prêt sur http://127.0.0.1:${PORT}${RESET}"
echo -e "${GREEN}  Compte : admin@edumanager.local${RESET}"
echo -e "${GREEN}══════════════════════════════════════════════${RESET}"

echo ""

exec python manage.py runserver 0.0.0.0:$PORT