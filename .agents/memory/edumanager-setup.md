---
name: EduManager project setup
description: Key facts about the school management system — how to run it, what's built, what's incomplete
---

# EduManager — Project Context

## How to Run
- Workflow: `PORT=5000 bash run.sh` (runs migrations + collectstatic + creates super admin + starts server)
- Seed data: `python seed_test_data.py` (idempotent; creates 2 schools, 10 school users, 40 students, payments)
- Default super admin: `admin@edumanager.local` / `Admin@2024!`

## Architecture Rules
- Multi-tenant: ALL querysets must filter by `request.user.school` (super_admin sees all with no school filter)
- Role-based access via `@role_required(['admin_ecole', ...])` decorator in `apps/authentication/decorators.py`
- No Django Admin for business data — custom dashboard only
- First-login password change enforced via `FirstLoginMiddleware` + `must_change_password` flag

## What's Complete (V1.1)
- Auth (login/logout/change-password/first-login flow)
- Schools CRUD (super admin only)
- Users CRUD with role assignment
- Students full CRUD + detail
- Parents list/create/edit
- Staff full CRUD (list/create/edit/detail/toggle) — completed in V1.1
- Academic (years, levels, classrooms, subjects)
- Finance (payments list + create)
- Enrollment (list + create)
- Audit log
- Role-based dashboards for all 5 roles (with welcome headers + stats + quick links)
- Error pages (403, 404, 500) via `apps/dashboard/error_views.py`
- Sidebar active link bug fixed (was comparing path to URL name, now uses `{% url ... as var %}`)

## What's Stub (not yet fully built)
- Timetable — index only, no create/manage UI
- Assessments — index + create form, no grade entry per student
- Reports (bulletins) — index only
- Analytics — index only
- Backup — index + create (basic)
- Communication — index only
- Documents — index only
- Transport — index only

## Key Quirks
- Database: SQLite via `--run-syncdb` (no migration files); tables recreated on each fresh DB
- `seed_test_data.py` must NOT be wrapped in a single `@transaction.atomic` — finance section failure can roll back all schools/users
- `Student.student_id` is globally unique (not per-school), so seed IDs use `EL{school_pk:02d}{i:04d}` format
- `Classroom` requires a `Level` ForeignKey (not a plain string field)
- `Payment.payment_date` has `default=timezone.now` but passing `None` overrides it — omit the key for non-paid statuses

**Why:** These were discovered during V1.1 implementation and seed script debugging.
