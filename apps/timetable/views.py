"""Timetable module views."""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from apps.authentication.decorators import role_required
from apps.audit.utils import log_action
from apps.academic.models import Classroom, Subject
from apps.users.models import User, Role

from .models import TimeSlot, TimetableSchedule, TimetableEntry, SchoolConfig, DAYS
from .forms import TimeSlotForm, TimetableEntryForm


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_school(request):
    return request.user.school


def _get_working_days(school):
    """Return the list of (day_index, day_label) for this school's configured days."""
    try:
        config = school.timetable_config
        return config.get_working_days()
    except SchoolConfig.DoesNotExist:
        return [(i, label) for i, label in DAYS if i in (0, 1, 2, 3, 4)]


def _get_or_create_config(school):
    config, _ = SchoolConfig.objects.get_or_create(
        school=school,
        defaults={'working_days': [0, 1, 2, 3, 4]}
    )
    return config


def _check_conflicts(school, classroom, day, timeslot, teacher_id=None, room='', exclude_pk=None):
    """Returns a list of conflict description strings."""
    conflicts = []
    base_qs = TimetableEntry.objects.filter(school=school, day=day, timeslot=timeslot)
    if exclude_pk:
        base_qs = base_qs.exclude(pk=exclude_pk)

    # Teacher conflict
    if teacher_id:
        qs = base_qs.filter(teacher_id=teacher_id).exclude(classroom=classroom)
        if qs.exists():
            other = qs.select_related('classroom').first()
            conflicts.append(
                f"L'enseignant est déjà affecté à la classe {other.classroom} sur ce créneau."
            )

    # Room conflict
    if room and room.strip():
        qs = base_qs.filter(room__iexact=room.strip()).exclude(classroom=classroom)
        if qs.exists():
            other = qs.select_related('classroom').first()
            conflicts.append(
                f"La salle « {room.strip()} » est déjà utilisée par {other.classroom} sur ce créneau."
            )

    return conflicts


def _build_grid(school, classroom, timeslots, days_list, entries_qs=None):
    """Build a matrix {timeslot_id: {day: entry_or_None}} for rendering."""
    if entries_qs is None:
        entries_qs = TimetableEntry.objects.filter(
            school=school, classroom=classroom
        ).select_related('subject', 'teacher', 'timeslot')

    entry_map = {}
    for e in entries_qs:
        entry_map[(e.timeslot_id, e.day)] = e

    grid = []
    for slot in timeslots:
        row = {'slot': slot, 'cells': []}
        for day_num, day_label in days_list:
            row['cells'].append({
                'day': day_num,
                'day_label': day_label,
                'entry': entry_map.get((slot.pk, day_num)),
            })
        grid.append(row)
    return grid


def _build_teacher_grid(school, teacher, timeslots, days_list, classroom_ids=None):
    """Build a matrix for teacher's personal schedule."""
    qs = TimetableEntry.objects.filter(
        school=school, teacher=teacher
    ).select_related('subject', 'classroom', 'timeslot')

    # Optionally restrict to specific classrooms (e.g. published only)
    if classroom_ids is not None:
        qs = qs.filter(classroom_id__in=classroom_ids)

    entry_map = {}
    for e in qs:
        entry_map[(e.timeslot_id, e.day)] = e

    grid = []
    for slot in timeslots:
        row = {'slot': slot, 'cells': []}
        for day_num, day_label in days_list:
            row['cells'].append({
                'day': day_num,
                'day_label': day_label,
                'entry': entry_map.get((slot.pk, day_num)),
            })
        grid.append(row)
    return grid


def _published_classroom_ids(school):
    """Return a set of classroom PKs whose timetable is published."""
    return set(
        TimetableSchedule.objects.filter(school=school, status='published')
        .values_list('classroom_id', flat=True)
    )


# ── Main Index ──────────────────────────────────────────────────────────────

@login_required
@role_required(['admin_ecole', 'secretaire', 'enseignant', 'super_admin'])
def index(request):
    """Main hub — dispatches by role."""
    user = request.user
    school = _get_school(request)

    if user.role == Role.ENSEIGNANT:
        return teacher_timetable(request)

    # Secretary or Director
    classrooms = Classroom.objects.filter(school=school).select_related('level', 'academic_year')
    teachers = User.objects.filter(school=school, role=Role.ENSEIGNANT, is_active=True)

    # Build schedule status map
    schedules = {
        s.classroom_id: s
        for s in TimetableSchedule.objects.filter(school=school)
    }

    classroom_data = []
    for cls in classrooms:
        sched = schedules.get(cls.pk)
        entry_count = TimetableEntry.objects.filter(school=school, classroom=cls).count()
        classroom_data.append({
            'classroom': cls,
            'schedule': sched,
            'entry_count': entry_count,
        })

    can_manage = user.role in (Role.SECRETAIRE,)
    has_timeslots = TimeSlot.objects.filter(school=school).exists()

    return render(request, 'timetable/index.html', {
        'classroom_data': classroom_data,
        'teachers': teachers,
        'can_manage': can_manage,
        'has_timeslots': has_timeslots,
        'title': 'Emplois du temps',
    })


# ── Schedule Configuration (Secretary only) ─────────────────────────────────

@login_required
@role_required(['secretaire'])
def schedule_config(request):
    """Manage time slots, breaks, and working days for the school."""
    school = _get_school(request)
    config = _get_or_create_config(school)

    if request.method == 'POST':
        action = request.POST.get('action', 'add_slot')

        if action == 'save_days':
            # Save working days configuration
            selected_days = [int(d) for d in request.POST.getlist('working_days') if d.isdigit()]
            if not selected_days:
                messages.error(request, "Sélectionnez au moins un jour de cours.")
            else:
                config.working_days = sorted(selected_days)
                config.save()
                log_action(request.user, 'UPDATE', f"Jours de cours mis à jour: {selected_days}", config)
                messages.success(request, "Jours de cours enregistrés.")
            return redirect('timetable:schedule_config')

        # Default: add a timeslot
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.school = school
            if not slot.name:
                slot.name = slot.time_range
            slot.save()
            log_action(request.user, 'CREATE', f"Créneau ajouté: {slot}", slot)
            messages.success(request, f"Créneau {slot.time_range} ajouté.")
            return redirect('timetable:schedule_config')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        last_order = TimeSlot.objects.filter(school=school).count()
        form = TimeSlotForm(initial={'order': last_order})

    timeslots = TimeSlot.objects.filter(school=school)
    all_days = list(DAYS)
    working_days = config.working_days or [0, 1, 2, 3, 4]

    return render(request, 'timetable/schedule_config.html', {
        'form': form,
        'timeslots': timeslots,
        'all_days': all_days,
        'working_days': working_days,
        'title': 'Configuration des horaires',
    })


@login_required
@role_required(['secretaire'])
def timeslot_edit(request, pk):
    school = _get_school(request)
    slot = get_object_or_404(TimeSlot, pk=pk, school=school)

    if request.method == 'POST':
        form = TimeSlotForm(request.POST, instance=slot)
        if form.is_valid():
            updated = form.save(commit=False)
            if not updated.name:
                updated.name = updated.time_range
            updated.save()
            log_action(request.user, 'UPDATE', f"Créneau modifié: {slot}", slot)
            messages.success(request, "Créneau modifié.")
            return redirect('timetable:schedule_config')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = TimeSlotForm(instance=slot)

    return render(request, 'timetable/timeslot_form.html', {
        'form': form,
        'slot': slot,
        'title': 'Modifier le créneau',
    })


@login_required
@role_required(['secretaire'])
@require_POST
def timeslot_delete(request, pk):
    school = _get_school(request)
    slot = get_object_or_404(TimeSlot, pk=pk, school=school)
    name = str(slot)
    slot.delete()
    log_action(request.user, 'DELETE', f"Créneau supprimé: {name}")
    messages.success(request, f"Créneau « {name} » supprimé.")
    return redirect('timetable:schedule_config')


# ── Classroom Timetable Grid ────────────────────────────────────────────────

@login_required
@role_required(['admin_ecole', 'secretaire', 'super_admin'])
def classroom_timetable(request, classroom_id):
    """Display the timetable grid for a specific classroom."""
    school = _get_school(request)
    classroom = get_object_or_404(Classroom, pk=classroom_id, school=school)

    timeslots = TimeSlot.objects.filter(school=school)
    if not timeslots.exists():
        messages.warning(request, "Configurez d'abord les créneaux horaires.")
        if request.user.role == Role.SECRETAIRE:
            return redirect('timetable:schedule_config')
        return redirect('timetable:index')

    can_manage = request.user.role in (Role.SECRETAIRE,)

    # Get or create the schedule status object
    if can_manage:
        schedule, _ = TimetableSchedule.objects.get_or_create(
            school=school, classroom=classroom,
            defaults={'created_by': request.user}
        )
    else:
        schedule = TimetableSchedule.objects.filter(school=school, classroom=classroom).first()

    # --- Publication enforcement for non-secretary ---
    not_published = False
    entries_qs = None
    if not can_manage:
        if schedule is None or not schedule.is_published:
            not_published = True
            # Build empty grid — no entries
            entries_qs = TimetableEntry.objects.none()
        # else entries_qs stays None → _build_grid will query normally

    days_to_show = _get_working_days(school)
    grid = _build_grid(school, classroom, timeslots, days_to_show, entries_qs=entries_qs)

    subjects = classroom.subjects.filter(school=school)
    teachers = User.objects.filter(school=school, role=Role.ENSEIGNANT, is_active=True)

    return render(request, 'timetable/classroom_timetable.html', {
        'classroom': classroom,
        'grid': grid,
        'days': days_to_show,
        'timeslots': timeslots,
        'can_manage': can_manage,
        'schedule': schedule,
        'subjects': subjects,
        'teachers': teachers,
        'not_published': not_published,
        'title': f"Emploi du temps — {classroom.name}",
    })


# ── Entry CRUD (Secretary only) ─────────────────────────────────────────────

@login_required
@role_required(['secretaire'])
def entry_add(request, classroom_id):
    """Add a course entry (AJAX-friendly POST only)."""
    school = _get_school(request)
    classroom = get_object_or_404(Classroom, pk=classroom_id, school=school)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        day = request.POST.get('day')
        timeslot_id = request.POST.get('timeslot_id')
        subject_id = request.POST.get('subject')
        teacher_id = request.POST.get('teacher') or None
        room = request.POST.get('room', '').strip()

        errors = []

        if not day or not timeslot_id or not subject_id:
            errors.append("Jour, créneau et matière sont obligatoires.")

        timeslot = None
        subject = None

        if not errors:
            # Validate timeslot belongs to school and is a course slot
            timeslot = TimeSlot.objects.filter(pk=timeslot_id, school=school, slot_type='course').first()
            if not timeslot:
                errors.append("Créneau invalide.")

        if not errors:
            # --- Strict: subject must be assigned to this classroom ---
            subject = classroom.subjects.filter(pk=subject_id, school=school).first()
            if not subject:
                errors.append("Cette matière n'est pas assignée à cette classe.")

        if not errors:
            # --- Strict: teacher must belong to this school and have role enseignant ---
            teacher = None
            if teacher_id:
                teacher = User.objects.filter(
                    pk=teacher_id, school=school, role=Role.ENSEIGNANT, is_active=True
                ).first()
                if not teacher:
                    errors.append("Cet enseignant n'appartient pas à votre école.")

        if not errors:
            # Class conflict (unique_together enforced at DB level, check first)
            if TimetableEntry.objects.filter(classroom=classroom, day=day, timeslot=timeslot).exists():
                errors.append("Cette classe a déjà un cours sur ce créneau.")

        if not errors:
            conflicts = _check_conflicts(school, classroom, int(day), timeslot, teacher_id, room)
            errors.extend(conflicts)

        if errors:
            if is_ajax:
                return JsonResponse({'ok': False, 'errors': errors}, status=400)
            for e in errors:
                messages.error(request, e)
            return redirect('timetable:classroom_timetable', classroom_id=classroom_id)

        teacher = User.objects.filter(pk=teacher_id, school=school).first() if teacher_id else None

        entry = TimetableEntry.objects.create(
            school=school,
            classroom=classroom,
            subject=subject,
            teacher=teacher,
            day=int(day),
            timeslot=timeslot,
            room=room,
        )

        # Advance schedule status to "preparing" if still draft
        sched, _ = TimetableSchedule.objects.get_or_create(
            school=school, classroom=classroom,
            defaults={'created_by': request.user}
        )
        if sched.status == 'draft':
            sched.status = 'preparing'
            sched.save()

        log_action(request.user, 'CREATE', f"Cours ajouté: {entry}", entry)

        if is_ajax:
            return JsonResponse({
                'ok': True,
                'entry': {
                    'pk': entry.pk,
                    'subject': entry.subject.name,
                    'subject_color': entry.subject.color,
                    'teacher': entry.teacher.get_full_name() if entry.teacher else '',
                    'room': entry.room,
                    'day': entry.day,
                    'timeslot_id': entry.timeslot_id,
                }
            })

        messages.success(request, "Cours ajouté.")
        return redirect('timetable:classroom_timetable', classroom_id=classroom_id)

    return redirect('timetable:classroom_timetable', classroom_id=classroom_id)


@login_required
@role_required(['secretaire'])
def entry_edit(request, pk):
    """Edit a course entry."""
    school = _get_school(request)
    entry = get_object_or_404(TimetableEntry, pk=pk, school=school)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        teacher_id = request.POST.get('teacher') or None
        room = request.POST.get('room', '').strip()

        errors = []

        if not subject_id:
            errors.append("La matière est obligatoire.")

        subject = None
        if not errors:
            # --- Strict: subject must be assigned to the classroom ---
            subject = entry.classroom.subjects.filter(pk=subject_id, school=school).first()
            if not subject:
                errors.append("Cette matière n'est pas assignée à cette classe.")

        if not errors and teacher_id:
            # --- Strict: teacher must belong to school ---
            teacher_obj = User.objects.filter(
                pk=teacher_id, school=school, role=Role.ENSEIGNANT, is_active=True
            ).first()
            if not teacher_obj:
                errors.append("Cet enseignant n'appartient pas à votre école.")

        if not errors:
            conflicts = _check_conflicts(
                school, entry.classroom, entry.day, entry.timeslot,
                teacher_id, room, exclude_pk=pk
            )
            errors.extend(conflicts)

        if errors:
            if is_ajax:
                return JsonResponse({'ok': False, 'errors': errors}, status=400)
            for e in errors:
                messages.error(request, e)
            return redirect('timetable:classroom_timetable', classroom_id=entry.classroom_id)

        teacher = User.objects.filter(pk=teacher_id, school=school).first() if teacher_id else None

        entry.subject = subject
        entry.teacher = teacher
        entry.room = room
        entry.save()

        log_action(request.user, 'UPDATE', f"Cours modifié: {entry}", entry)

        if is_ajax:
            return JsonResponse({
                'ok': True,
                'entry': {
                    'pk': entry.pk,
                    'subject': entry.subject.name,
                    'subject_color': entry.subject.color,
                    'teacher': entry.teacher.get_full_name() if entry.teacher else '',
                    'room': entry.room,
                    'day': entry.day,
                    'timeslot_id': entry.timeslot_id,
                }
            })

        messages.success(request, "Cours modifié.")
        return redirect('timetable:classroom_timetable', classroom_id=entry.classroom_id)

    # GET: return entry data for the modal
    if is_ajax:
        return JsonResponse({
            'ok': True,
            'entry': {
                'pk': entry.pk,
                'subject_id': entry.subject_id,
                'teacher_id': entry.teacher_id,
                'room': entry.room,
                'day': entry.day,
                'timeslot_id': entry.timeslot_id,
                'classroom_id': entry.classroom_id,
            }
        })

    return redirect('timetable:classroom_timetable', classroom_id=entry.classroom_id)


@login_required
@role_required(['secretaire'])
@require_POST
def entry_delete(request, pk):
    """Delete a course entry."""
    school = _get_school(request)
    entry = get_object_or_404(TimetableEntry, pk=pk, school=school)
    classroom_id = entry.classroom_id
    label = str(entry)
    entry.delete()
    log_action(request.user, 'DELETE', f"Cours supprimé: {label}")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})

    messages.success(request, "Cours supprimé.")
    return redirect('timetable:classroom_timetable', classroom_id=classroom_id)


# ── Schedule Status (Secretary only) ───────────────────────────────────────

@login_required
@role_required(['secretaire'])
@require_POST
def schedule_publish(request, classroom_id):
    """Change the publication status of a classroom's timetable."""
    school = _get_school(request)
    classroom = get_object_or_404(Classroom, pk=classroom_id, school=school)
    action = request.POST.get('action', 'publish')

    sched, _ = TimetableSchedule.objects.get_or_create(
        school=school, classroom=classroom,
        defaults={'created_by': request.user}
    )

    if action == 'publish':
        sched.publish(user=request.user)
        log_action(request.user, 'UPDATE', f"Emploi du temps publié: {classroom.name}", sched)
        messages.success(request, f"L'emploi du temps de {classroom.name} est publié.")
    elif action == 'draft':
        sched.status = 'draft'
        sched.published_at = None
        sched.save()
        messages.info(request, f"L'emploi du temps de {classroom.name} est repassé en brouillon.")
    elif action == 'preparing':
        sched.status = 'preparing'
        sched.save()
        messages.info(request, "Statut mis à jour : En préparation.")

    return redirect('timetable:classroom_timetable', classroom_id=classroom_id)


# ── Teacher Timetable ───────────────────────────────────────────────────────

@login_required
@role_required(['admin_ecole', 'secretaire', 'enseignant', 'super_admin'])
def teacher_timetable(request, teacher_id=None):
    """Display a teacher's personal schedule."""
    school = _get_school(request)
    user = request.user

    # Determine which teacher to show
    if user.role == Role.ENSEIGNANT:
        teacher = user
    elif teacher_id:
        teacher = get_object_or_404(User, pk=teacher_id, school=school, role=Role.ENSEIGNANT)
    else:
        # Director without teacher_id → show teacher list
        teachers = User.objects.filter(school=school, role=Role.ENSEIGNANT, is_active=True)
        return render(request, 'timetable/teacher_list.html', {
            'teachers': teachers,
            'title': 'Emplois du temps des enseignants',
        })

    timeslots = TimeSlot.objects.filter(school=school)
    days_to_show = _get_working_days(school)

    # --- Publication enforcement ---
    # Teachers and directors only see entries from PUBLISHED classroom timetables.
    # Secretaries see all.
    if user.role in (Role.ENSEIGNANT, Role.ADMIN_ECOLE):
        pub_ids = _published_classroom_ids(school)
        # Pass published classroom IDs to filter entries
        grid = _build_teacher_grid(school, teacher, timeslots, days_to_show, classroom_ids=pub_ids)
    else:
        grid = _build_teacher_grid(school, teacher, timeslots, days_to_show)

    is_print = request.GET.get('print') == '1'
    template = 'timetable/print_timetable.html' if is_print else 'timetable/teacher_timetable.html'

    return render(request, template, {
        'teacher': teacher,
        'grid': grid,
        'days': days_to_show,
        'timeslots': timeslots,
        'title': f"Emploi du temps — {teacher.get_full_name()}",
        'school': school,
    })


# ── Print / PDF ─────────────────────────────────────────────────────────────

@login_required
@role_required(['admin_ecole', 'secretaire', 'enseignant', 'super_admin'])
def print_classroom_timetable(request, classroom_id):
    """Print-optimized view for a classroom's timetable."""
    school = _get_school(request)
    classroom = get_object_or_404(Classroom, pk=classroom_id, school=school)
    can_manage = request.user.role in (Role.SECRETAIRE,)

    # Publication enforcement for non-secretary
    if not can_manage:
        schedule = TimetableSchedule.objects.filter(school=school, classroom=classroom).first()
        if schedule is None or not schedule.is_published:
            messages.warning(request, "Cet emploi du temps n'est pas encore publié.")
            return redirect('timetable:index')

    timeslots = TimeSlot.objects.filter(school=school)
    days_to_show = _get_working_days(school)
    grid = _build_grid(school, classroom, timeslots, days_to_show)

    return render(request, 'timetable/print_classroom_timetable.html', {
        'classroom': classroom,
        'grid': grid,
        'days': days_to_show,
        'school': school,
        'title': f"Emploi du temps — {classroom.name}",
    })
