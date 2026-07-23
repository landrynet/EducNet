---
name: EduManager project setup
description: Key facts about the school management system — how to run it, what's built, what's incomplete
---

# EduManager — Project Context

## How to Run
- Workflow: `PORT=5000 bash run.sh` (runs migrations + collectstatic + creates super admin + starts server)
- Seed data: `python seed_test_data.py` (idempotent; creates 2 schools, 10 users, classrooms, subjects, staff profiles, timetable entries)
- Default super admin: `admin@edumanager.local` / `Admin@2024!`

## Architecture Rules
- Multi-tenant: ALL querysets must filter by `request.user.school` (super_admin sees all with no school filter)
- Role-based access via `@role_required(['admin_ecole', ...])` decorator in `apps/authentication/decorators.py`
- No Django Admin for business data — custom dashboard only
- First-login password change enforced via `FirstLoginMiddleware` + `must_change_password` flag

## What's Complete (V1.5 — Étape 2: Timetable)
- Auth (login/logout/change-password/first-login flow)
- Schools CRUD (super admin) + Settings (admin_ecole) with read-only type display
- Matricule config UI in school settings
- Users CRUD with role assignment
- Students full CRUD + detail
- Parents list/create/edit
- Staff full CRUD + subjects assignment per teacher (M2M, school-scoped)
- Academic: years, levels, classrooms (with subjects M2M), subjects (with edit view)
- Classroom detail view with subject list + teacher panel
- Finance (payments list + create)
- Enrollment (list + create)
- Audit log
- Role-based dashboards for all 5 roles
- Error pages (403, 404, 500)
- Sidebar shows school name + school type
- **Timetable module (Étape 2)**:
  - Secretary: configure timeslots/breaks, create/edit/delete course entries, publish timetable, conflict detection
  - Director/admin_ecole: read-only view of all classroom and teacher schedules
  - Teacher: personal timetable view + print/PDF
  - AJAX modal-based entry creation with real-time conflict feedback
  - Print-optimized templates for both classroom and teacher views

## What's Stub (not yet fully built)
- Assessments — index + create form, no grade entry per student
- Reports (bulletins) — index only
- Analytics — index only
- Backup — index + create (basic)
- Communication — index only
- Documents — index only
- Transport — index only

## Key Quirks
- Database: SQLite. Most apps (academic, staff, users, timetable now) have migrations. `timetable` moved from syncdb to proper migrations in Étape 2.
- `academic_classroom_subjects` M2M table: NOT auto-created by syncdb on existing DBs. run.sh creates it via `CREATE TABLE IF NOT EXISTS` after migrations step.
- `students_matriculeconfig.include_initials`: added via migration `0003` — pass `first_name`/`last_name` to `generate_next()` when initials are enabled.
- `seed_test_data.py` must NOT be wrapped in `@transaction.atomic` — finance failure can roll back all schools/users.
- `Classroom` requires a `Level` ForeignKey (not a plain string field).
- `Payment.payment_date` has `default=timezone.now` but passing `None` overrides it — omit the key for non-paid statuses.
- `StaffProfileForm` requires `school=` kwarg for subject queryset isolation.
- `ClassroomForm` requires `school=` kwarg for subject/year/level/teacher querysets.
- `classroom_create` must call `form.save_m2m()` after `cls.save()` (commit=False pattern).
- Timetable entry add/edit uses AJAX (X-Requested-With: XMLHttpRequest) returning JSON; non-AJAX falls back to redirect. `entry_add` is a POST-only view under `/timetable/classe/<id>/entry/add/`.
- Timetable validation must enforce both configured working days and the teacher's assigned subjects; the seed script must preserve existing students and keep seeded teacher-subject relations valid when rerun.
- On Windows Git Bash, avoid comparing captured shell output as plain text; use process exit codes because CRLF can turn a valid marker into a false negative.
- Legacy timetable databases may have the right tables but missing newer columns such as `slot_type`; startup repair must add missing fields idempotently, not only missing tables.

**Why:** Discovered during V1.1–V1.5 implementation and debugging.
