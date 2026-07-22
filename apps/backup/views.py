import os
import subprocess
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse
from django.conf import settings
from apps.authentication.decorators import role_required
from apps.audit.utils import log_action


@login_required
@role_required(['super_admin', 'admin_ecole'])
def backup_index(request):
    """Show available backups and allow creating new ones."""
    backup_dir = settings.BASE_DIR / 'backups'
    backup_dir.mkdir(exist_ok=True)
    backups = sorted(
        [f for f in backup_dir.iterdir() if f.suffix == '.sqlite3'],
        key=lambda x: x.stat().st_mtime, reverse=True
    )
    return render(request, 'backup/index.html', {
        'backups': [{'name': b.name, 'size': b.stat().st_size, 'date': datetime.fromtimestamp(b.stat().st_mtime)} for b in backups],
        'title': 'Sauvegarde & Restauration',
    })


@login_required
@role_required(['super_admin', 'admin_ecole'])
def backup_create(request):
    """Create a database backup."""
    if request.method == 'POST':
        backup_dir = settings.BASE_DIR / 'backups'
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"backup_{timestamp}.sqlite3"
        db_path = settings.DATABASES['default']['NAME']
        try:
            import shutil
            shutil.copy2(db_path, backup_file)
            log_action(request.user, 'OTHER', f"Sauvegarde créée: {backup_file.name}", request.user)
            messages.success(request, f"Sauvegarde créée: {backup_file.name}")
        except Exception as e:
            messages.error(request, f"Erreur de sauvegarde: {e}")
    return redirect('backup:index')
