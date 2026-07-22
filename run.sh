#!/bin/bash
# EduManager — Script de démarrage V1.1
# ─────────────────────────────────────────────────────────────
# Ce script :
#   1. Crée ou active l'environnement virtuel Python (.venv)
#   2. Installe / met à jour les dépendances depuis requirements.txt
#   3. Applique les migrations de base de données
#   4. Collecte les fichiers statiques
#   5. Crée le Super Admin s'il n'existe pas
#   6. Charge les données de test (sans duplication si déjà présentes)
#   7. Démarre le serveur Django
# ─────────────────────────────────────────────────────────────

set -e
cd "$(dirname "$0")"

PORT=${PORT:-8000}
VENV_DIR=".venv"
REQ_FILE="requirements.txt"
REQ_HASH_FILE=".venv/.req_hash"

# ── Couleurs ──────────────────────────────────────────────────
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

log()  { echo -e "${BLUE}[EduManager]${RESET} $1"; }
ok()   { echo -e "${GREEN}[✓]${RESET} $1"; }
warn() { echo -e "${YELLOW}[!]${RESET} $1"; }

echo ""
echo -e "${BLUE}══════════════════════════════════════════════${RESET}"
echo -e "${BLUE}  EduManager V1.1 — Port $PORT${RESET}"
echo -e "${BLUE}══════════════════════════════════════════════${RESET}"
echo ""

# ── 1. Environnement virtuel ──────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    log "Création de l'environnement virtuel (.venv)..."
    python -m venv "$VENV_DIR" --system-site-packages
    ok "Environnement virtuel créé."
else
    ok "Environnement virtuel existant (.venv)."
fi

# Activation (neutralise PIP_USER imposé par certains hôtes)
source "$VENV_DIR/bin/activate"
export PIP_USER=0
ok "Environnement virtuel activé."

# ── 2. Dépendances (seulement si requirements.txt a changé) ───
CURRENT_HASH=""
SAVED_HASH=""

if command -v md5sum &>/dev/null; then
    CURRENT_HASH=$(md5sum "$REQ_FILE" 2>/dev/null | awk '{print $1}')
elif command -v md5 &>/dev/null; then
    CURRENT_HASH=$(md5 -q "$REQ_FILE" 2>/dev/null)
fi

[ -f "$REQ_HASH_FILE" ] && SAVED_HASH=$(cat "$REQ_HASH_FILE")

if [ "$CURRENT_HASH" != "$SAVED_HASH" ] || [ "$CURRENT_HASH" = "" ]; then
    log "Installation des dépendances depuis $REQ_FILE..."
    pip install -r "$REQ_FILE" --quiet --disable-pip-version-check
    [ -n "$CURRENT_HASH" ] && echo "$CURRENT_HASH" > "$REQ_HASH_FILE"
    ok "Dépendances installées / mises à jour."
else
    ok "Dépendances déjà à jour (requirements.txt inchangé)."
fi

# ── 3. Migrations ─────────────────────────────────────────────
log "Application des migrations..."
python manage.py migrate --run-syncdb 2>&1 \
  | grep -E "^(  Applying|  Creating|  Synchroni|Running|OK)" \
  | head -20 || true
ok "Migrations terminées."

# ── 4. Fichiers statiques ─────────────────────────────────────
log "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput 2>&1 | tail -1 || true
ok "Fichiers statiques collectés."

# ── 5. Super Admin ────────────────────────────────────────────
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
    print('Super Admin créé : admin@edumanager.local / Admin@2024!')
else:
    print('Super Admin déjà présent.')
" 2>&1 || true

# ── 6. Données de test ────────────────────────────────────────
log "Chargement des données de test (sans duplication)..."
python seed_test_data.py 2>&1 \
  | grep -E "^\[(OK|WARN)\]|SEED COMPLETE|admin@|Test@2024" \
  | grep -v "déjà existe\|already exists" \
  || true

# ── 7. Démarrage du serveur ───────────────────────────────────
echo ""
echo -e "${GREEN}══════════════════════════════════════════════${RESET}"
echo -e "${GREEN}  Serveur prêt sur http://0.0.0.0:${PORT}${RESET}"
echo -e "${GREEN}  Compte : admin@edumanager.local / Admin@2024!${RESET}"
echo -e "${GREEN}══════════════════════════════════════════════${RESET}"
echo ""

exec python manage.py runserver 0.0.0.0:$PORT
