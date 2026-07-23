from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from apps.academic.models import AcademicYear, Classroom, Level, Subject
from apps.schools.models import School
from apps.staff.models import StaffProfile
from apps.users.models import Role, User

from .forms import TimeSlotForm, TimetableEntryForm
from .models import SchoolConfig, TimeSlot, TimetableEntry, TimetableSchedule


class TimetableTestBase(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(
            name='École A', code='TEST-A', address='Adresse A',
            city='Abidjan', country="Côte d'Ivoire",
        )
        self.school_b = School.objects.create(
            name='École B', code='TEST-B', address='Adresse B',
            city='Abidjan', country="Côte d'Ivoire",
        )
        self.secretary = self._user('secretaire-a@test.local', Role.SECRETAIRE, self.school_a)
        self.admin = self._user('admin-a@test.local', Role.ADMIN_ECOLE, self.school_a)
        self.teacher = self._user('teacher-a@test.local', Role.ENSEIGNANT, self.school_a)
        self.other_teacher = self._user(
            'teacher-b@test.local', Role.ENSEIGNANT, self.school_a,
        )
        self.foreign_teacher = self._user(
            'teacher-b-school@test.local', Role.ENSEIGNANT, self.school_b,
        )
        year = AcademicYear.objects.create(
            school=self.school_a, name='2025-2026',
            start_date=date(2025, 9, 1), end_date=date(2026, 7, 31),
            is_current=True,
        )
        level = Level.objects.create(school=self.school_a, name='6ème', order=1)
        self.classroom = Classroom.objects.create(
            school=self.school_a, academic_year=year, level=level, name='6ème A',
        )
        self.other_classroom = Classroom.objects.create(
            school=self.school_a, academic_year=year, level=level, name='6ème B',
        )
        self.subject = Subject.objects.create(
            school=self.school_a, name='Mathématiques', code='MATH',
        )
        self.foreign_subject = Subject.objects.create(
            school=self.school_b, name='Matière étrangère', code='FOREIGN',
        )
        self.classroom.subjects.add(self.subject)
        self.other_classroom.subjects.add(self.subject)
        self.teacher_profile = StaffProfile.objects.create(
            user=self.teacher, school=self.school_a, staff_type='teacher',
        )
        self.teacher_profile.subjects.add(self.subject)
        self.other_teacher_profile = StaffProfile.objects.create(
            user=self.other_teacher, school=self.school_a, staff_type='teacher',
        )
        self.other_teacher_profile.subjects.add(self.subject)
        self.slot = TimeSlot.objects.create(
            school=self.school_a, name='Cours 1',
            start_time=time(8), end_time=time(9), order=1,
        )
        self.other_slot = TimeSlot.objects.create(
            school=self.school_a, name='Cours 2',
            start_time=time(9), end_time=time(10), order=2,
        )

    @staticmethod
    def _user(email, role, school):
        return User.objects.create_user(
            email=email, password='Test@2024!', first_name='Test',
            last_name=role, role=role, school=school,
            must_change_password=False, profile_completed=True,
        )

    def _login(self, user):
        self.client.force_login(user)

    def _entry_data(self, **overrides):
        data = {
            'day': '0',
            'timeslot_id': str(self.slot.pk),
            'subject': str(self.subject.pk),
            'teacher': str(self.teacher.pk),
            'room': 'Salle 1',
        }
        data.update(overrides)
        return data


class TimetableValidationTests(TimetableTestBase):
    def test_entry_form_only_lists_teachers_assigned_to_selected_subject(self):
        other_subject = Subject.objects.create(
            school=self.school_a, name='Français', code='FR',
        )
        self.classroom.subjects.add(other_subject)
        form = TimetableEntryForm(
            data={'subject': str(self.subject.pk)},
            school=self.school_a,
            classroom=self.classroom,
        )
        teacher_values = {str(value) for value, _ in form.fields['teacher'].choices}
        self.assertIn(str(self.teacher.pk), teacher_values)
        self.assertIn(str(self.other_teacher.pk), teacher_values)
        self.assertNotIn(str(self.foreign_teacher.pk), teacher_values)

        form = TimetableEntryForm(
            data={'subject': str(other_subject.pk), 'teacher': str(self.teacher.pk)},
            school=self.school_a,
            classroom=self.classroom,
        )
        self.assertFalse(form.is_valid())

    def test_teacher_detail_link_is_available_without_exposing_platform_user_list(self):
        self._login(self.admin)
        response = self.client.get(
            reverse('staff:detail', args=[self.teacher_profile.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('users:detail', args=[self.teacher.pk]))

        detail = self.client.get(reverse('users:detail', args=[self.teacher.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, self.teacher.email)

    def test_timeslot_overlap_is_rejected_only_within_same_school(self):
        form = TimeSlotForm(
            data={
                'start_time': '08:30', 'end_time': '09:30',
                'slot_type': 'course', 'name': 'Chevauchement', 'order': 3,
            },
            school=self.school_a,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('chevauche', str(form.errors).lower())

        foreign_form = TimeSlotForm(
            data={
                'start_time': '08:30', 'end_time': '09:30',
                'slot_type': 'course', 'name': 'École B', 'order': 1,
            },
            school=self.school_b,
        )
        self.assertTrue(foreign_form.is_valid())

    def test_invalid_day_returns_clear_ajax_error(self):
        self._login(self.secretary)
        response = self.client.post(
            reverse('timetable:entry_add', args=[self.classroom.pk]),
            self._entry_data(day='99'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Jour, créneau', response.json()['errors'][0])
        self.assertEqual(TimetableEntry.objects.count(), 0)

    def test_teacher_class_and_room_conflicts_are_blocked(self):
        self._login(self.secretary)
        first = self.client.post(
            reverse('timetable:entry_add', args=[self.classroom.pk]),
            self._entry_data(),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(first.status_code, 200)

        teacher_conflict = self.client.post(
            reverse('timetable:entry_add', args=[self.other_classroom.pk]),
            self._entry_data(room='Salle 2'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(teacher_conflict.status_code, 400)
        self.assertIn('enseignant', teacher_conflict.json()['errors'][0].lower())

        room_conflict = self.client.post(
            reverse('timetable:entry_add', args=[self.other_classroom.pk]),
            self._entry_data(teacher=str(self.other_teacher.pk)),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(room_conflict.status_code, 400)
        self.assertIn('salle', room_conflict.json()['errors'][0].lower())

        class_conflict = self.client.post(
            reverse('timetable:entry_add', args=[self.classroom.pk]),
            self._entry_data(teacher=str(self.other_teacher.pk), room='Salle 3'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(class_conflict.status_code, 400)
        self.assertIn('classe', class_conflict.json()['errors'][0].lower())
        self.assertEqual(TimetableEntry.objects.count(), 1)

    def test_foreign_school_values_cannot_be_submitted(self):
        self._login(self.secretary)
        response = self.client.post(
            reverse('timetable:entry_add', args=[self.classroom.pk]),
            self._entry_data(
                subject=str(self.foreign_subject.pk),
                teacher=str(self.foreign_teacher.pk),
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('matière', response.json()['errors'][0].lower())
        self.assertEqual(TimetableEntry.objects.count(), 0)

    def test_teacher_must_be_assigned_to_selected_subject(self):
        unassigned = Subject.objects.create(
            school=self.school_a, name='Français', code='FR',
        )
        self.classroom.subjects.add(unassigned)
        self._login(self.secretary)
        response = self.client.post(
            reverse('timetable:entry_add', args=[self.classroom.pk]),
            self._entry_data(subject=str(unassigned.pk)),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('affecté', response.json()['errors'][0])

    def test_non_working_day_is_rejected(self):
        SchoolConfig.objects.create(school=self.school_a, working_days=[0, 1, 2, 3, 4])
        self._login(self.secretary)
        response = self.client.post(
            reverse('timetable:entry_add', args=[self.classroom.pk]),
            self._entry_data(day='5'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('jour de cours', response.json()['errors'][0])
        self.assertEqual(TimetableEntry.objects.count(), 0)

    def test_break_slot_cannot_receive_a_course(self):
        break_slot = TimeSlot.objects.create(
            school=self.school_a, name='Pause', start_time=time(10),
            end_time=time(10, 30), slot_type='break', order=3,
        )
        self._login(self.secretary)
        response = self.client.post(
            reverse('timetable:entry_add', args=[self.classroom.pk]),
            self._entry_data(timeslot_id=str(break_slot.pk)),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Créneau invalide', response.json()['errors'][0])
        self.assertFalse(TimetableEntry.objects.filter(timeslot=break_slot).exists())

    def test_add_edit_delete_entry_persists_without_deleting_timeslot(self):
        self._login(self.secretary)
        add_response = self.client.post(
            reverse('timetable:entry_add', args=[self.classroom.pk]),
            self._entry_data(),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(add_response.status_code, 200)
        entry = TimetableEntry.objects.get()
        self.assertEqual(entry.subject, self.subject)

        edit_response = self.client.post(
            reverse('timetable:entry_edit', args=[entry.pk]),
            {'subject': str(self.subject.pk), 'teacher': str(self.other_teacher.pk), 'room': 'Salle 9'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(edit_response.status_code, 200)
        entry.refresh_from_db()
        self.assertEqual(entry.teacher, self.other_teacher)
        self.assertEqual(entry.room, 'Salle 9')

        delete_response = self.client.post(
            reverse('timetable:entry_delete', args=[entry.pk]),
        )
        self.assertRedirects(
            delete_response,
            reverse('timetable:classroom_timetable', args=[self.classroom.pk]),
        )
        self.assertFalse(TimetableEntry.objects.filter(pk=entry.pk).exists())
        self.assertTrue(TimeSlot.objects.filter(pk=self.slot.pk).exists())

    def test_schedule_status_transitions_are_persisted(self):
        self._login(self.secretary)
        url = reverse('timetable:schedule_publish', args=[self.classroom.pk])
        for action, expected in (
            ('draft', 'draft'),
            ('preparing', 'preparing'),
            ('published', 'published'),
        ):
            response = self.client.post(url, {'action': action})
            self.assertRedirects(
                response,
                reverse('timetable:classroom_timetable', args=[self.classroom.pk]),
            )
            schedule = TimetableSchedule.objects.get(classroom=self.classroom)
            self.assertEqual(schedule.status, expected)
            page = self.client.get(
                reverse('timetable:classroom_timetable', args=[self.classroom.pk])
            )
            self.assertContains(page, schedule.get_status_display())
        self.client.logout()
        self._login(self.secretary)
        page = self.client.get(
            reverse('timetable:classroom_timetable', args=[self.classroom.pk])
        )
        self.assertContains(page, 'Publié')

    def test_only_secretary_can_change_status_or_entries(self):
        self._login(self.admin)
        status_response = self.client.post(
            reverse('timetable:schedule_publish', args=[self.classroom.pk]),
            {'action': 'published'},
        )
        self.assertRedirects(status_response, reverse('dashboard:index'))
        self.assertFalse(TimetableSchedule.objects.filter(classroom=self.classroom).exists())

        entry_response = self.client.post(
            reverse('timetable:entry_add', args=[self.classroom.pk]),
            self._entry_data(),
        )
        self.assertRedirects(entry_response, reverse('dashboard:index'))
        self.assertFalse(TimetableEntry.objects.exists())


class TimetablePermissionsAndOutputTests(TimetableTestBase):
    def test_admin_can_consult_but_cannot_manage(self):
        self._login(self.admin)
        config = self.client.get(reverse('timetable:schedule_config'))
        self.assertRedirects(config, reverse('dashboard:index'))
        classroom = self.client.get(
            reverse('timetable:classroom_timetable', args=[self.classroom.pk])
        )
        self.assertEqual(classroom.status_code, 200)
        self.assertNotContains(classroom, 'Ajouter un cours')

    def test_foreign_classroom_is_not_visible(self):
        foreign_year = AcademicYear.objects.create(
            school=self.school_b, name='2025-2026',
            start_date=date(2025, 9, 1), end_date=date(2026, 7, 31),
        )
        foreign_level = Level.objects.create(school=self.school_b, name='6ème')
        foreign_classroom = Classroom.objects.create(
            school=self.school_b, academic_year=foreign_year,
            level=foreign_level, name='Classe B',
        )
        self._login(self.admin)
        response = self.client.get(
            reverse('timetable:classroom_timetable', args=[foreign_classroom.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_teacher_pdf_download_contains_pdf_content(self):
        TimetableEntry.objects.create(
            school=self.school_a, classroom=self.classroom, subject=self.subject,
            teacher=self.teacher, day=0, timeslot=self.slot, room='Salle 1',
        )
        TimetableSchedule.objects.create(
            school=self.school_a, classroom=self.classroom,
            status='published', created_by=self.secretary,
        )
        self._login(self.teacher)
        response = self.client.get(
            reverse('timetable:teacher_pdf', args=[self.teacher.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_teacher_cannot_download_unpublished_class_pdf(self):
        self._login(self.admin)
        response = self.client.get(
            reverse('timetable:classroom_pdf', args=[self.classroom.pk])
        )
        self.assertRedirects(response, reverse('timetable:index'))

    def test_global_view_filters_unpublished_classes_for_admin(self):
        published_entry = TimetableEntry.objects.create(
            school=self.school_a, classroom=self.classroom, subject=self.subject,
            teacher=self.teacher, day=0, timeslot=self.slot, room='Salle 1',
        )
        unpublished_entry = TimetableEntry.objects.create(
            school=self.school_a, classroom=self.other_classroom, subject=self.subject,
            teacher=self.other_teacher, day=0, timeslot=self.other_slot, room='Salle 2',
        )
        TimetableSchedule.objects.create(
            school=self.school_a, classroom=self.classroom,
            status='published', created_by=self.secretary,
        )
        TimetableSchedule.objects.create(
            school=self.school_a, classroom=self.other_classroom,
            status='draft', created_by=self.secretary,
        )

        self._login(self.admin)
        admin_response = self.client.get(reverse('timetable:global'))
        self.assertEqual(admin_response.status_code, 200)
        self.assertContains(admin_response, self.classroom.name)
        self.assertNotContains(admin_response, self.other_classroom.name)

        self._login(self.secretary)
        secretary_response = self.client.get(reverse('timetable:global'))
        self.assertEqual(secretary_response.status_code, 200)
        self.assertContains(secretary_response, self.classroom.name)
        self.assertContains(secretary_response, self.other_classroom.name)