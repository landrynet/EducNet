# EduManager — Système de Gestion Scolaire Multi-Site

## Overview

EduManager is a multi-tenant school management system built with Django. Each school (tenant) has its own isolated data space. The system supports multiple user roles with role-based access control.

## Stack

- **Backend**: Python 3.12, Django 5.x, Django REST Framework
- **Frontend**: Bootstrap 5.3, Bootstrap Icons, Vanilla JS, Inter font
- **Database**: SQLite (development) — architecture is PostgreSQL-ready
- **Static files**: Whitenoise
- **Forms**: django-crispy-forms + crispy-bootstrap5

## Architecture

```
apps/
  users/          — Custom User model, role-based (email login)
  schools/        — Multi-tenant school entity (Super Admin only)
  authentication/ — Login, logout, first-login password change, decorators
  dashboard/      — Role-based dashboards (5 roles)
  students/       — Student CRUD with school isolation
  parents/        — Parent/guardian management
  staff/          — Staff profiles (teachers, admin, support)
  academic/       — Academic years, classrooms, subjects
  enrollment/     — Student enrollment management
  timetable/      — Class timetables
  assessments/    — Exams and grades
  reports/        — Report cards (bulletins)
  finance/        — Payments and fee management
  transport/      — School transport
  communication/  — Internal messaging
  documents/      — Document archive
  analytics/      — Statistics and reports
  audit/          — Action audit log
  backup/         — Database backup
```

## Roles

| Role | Description |
|------|-------------|
| `super_admin` | Platform-wide — manages all schools |
| `admin_ecole` | School admin — manages their school |
| `secretaire` | Administrative staff |
| `enseignant` | Teacher |
| `comptable` | Accountant |

## Running the App

```bash
PORT=5000 bash run.sh
```

`run.sh` automatically:
1. Runs database migrations
2. Collects static files
3. Creates a default Super Admin if none exists
4. Starts Django dev server on the specified PORT

**Default Super Admin**: `admin@edumanager.local` / `Admin@2024!`

## Seed Test Data

```bash
python seed_test_data.py
```

Creates 2 test schools with users for each role, students, staff, academic data, and payment records. See the script for test credentials.

## Key Files

- `config/settings.py` — Django settings
- `config/urls.py` — URL routing + custom error handlers (403, 404, 500)
- `run.sh` — Production-ready startup script
- `setup.sh` — First-time setup script
- `seed_test_data.py` — Test data generator
- `templates/base.html` — Base template (sidebar + navbar)
- `static/css/custom.css` — Design system CSS

## Security

- Role-based access via `@role_required` decorator
- School isolation: all querysets filtered by `request.user.school`
- First-login password change enforcement (`must_change_password` flag)
- Audit log on all important actions
- CSRF protection on all forms
- Session timeout: 8 hours

## User Preferences

- Language: French (fr-fr), Timezone: Africa/Abidjan
- No Django Admin for business data management — custom dashboard only
- Multi-tenant isolation must be preserved on all new views
