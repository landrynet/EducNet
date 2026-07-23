"""V1.4 tests — matricule uniqueness per school + auto-generation."""

from django.test import TestCase
from django.db import IntegrityError

from apps.schools.models import School
from apps.students.models import Student, MatriculeConfig


def _school(name, code=None):
    """Helper: create a school, optionally with an explicit code."""
    kwargs = dict(
        name=name,
        address='123 Rue Test',
        city='Abidjan',
        country="Côte d'Ivoire",
    )
    if code:
        kwargs['code'] = code
    return School.objects.create(**kwargs)


def _student(school, **kwargs):
    """Helper: create a student (matricule auto-generated)."""
    defaults = dict(
        first_name='Test',
        last_name='Élève',
        gender='M',
        date_of_birth='2010-01-01',
    )
    defaults.update(kwargs)
    return Student.objects.create(school=school, **defaults)


class SchoolCodeAutoGenerationTest(TestCase):
    """Requirement 4 — school code is auto-generated when not provided."""

    def test_code_generated_automatically(self):
        """A school created without a code receives SCH-XXXXXX automatically."""
        school = _school('École Test Auto')
        self.assertTrue(school.code.startswith('SCH-'), f"Expected SCH-* prefix, got '{school.code}'")
        self.assertEqual(len(school.code), 10)  # "SCH-" (4) + 6 digits

    def test_code_is_globally_unique(self):
        """Two auto-generated codes must differ."""
        s1 = _school('École Alpha')
        s2 = _school('École Beta')
        self.assertNotEqual(s1.code, s2.code)

    def test_explicit_code_preserved(self):
        """If a code is provided explicitly (e.g. from seed data), it is kept as-is."""
        school = _school('École Manuelle', code='CUSTOM-99')
        self.assertEqual(school.code, 'CUSTOM-99')

    def test_code_not_overwritten_on_save(self):
        """Saving an existing school must not regenerate the code."""
        school = _school('École Stable')
        original_code = school.code
        school.name = 'École Stable (modifiée)'
        school.save()
        school.refresh_from_db()
        self.assertEqual(school.code, original_code)


class MatriculePerSchoolUniquenessTest(TestCase):
    """Requirement 1 — matricule unique per school, not globally."""

    def setUp(self):
        self.school_a = _school('Lycée A', code='SCH-TEST-A')
        self.school_b = _school('Lycée B', code='SCH-TEST-B')

    def test_same_matricule_allowed_in_different_schools(self):
        """
        Req 1 & 6 (test 1): Two schools CAN share the same matricule.
        We bypass auto-generation by providing an explicit student_id.
        """
        s1 = Student.objects.create(
            school=self.school_a, student_id='2026-0001',
            first_name='Alice', last_name='Dupont',
            gender='F', date_of_birth='2010-01-01',
        )
        # Same matricule, different school → must succeed.
        s2 = Student.objects.create(
            school=self.school_b, student_id='2026-0001',
            first_name='Bob', last_name='Martin',
            gender='M', date_of_birth='2010-01-01',
        )
        self.assertEqual(s1.student_id, s2.student_id)
        self.assertNotEqual(s1.school, s2.school)

    def test_duplicate_matricule_rejected_in_same_school(self):
        """
        Req 1 & 6 (test 2): Duplicate matricule in the SAME school must be rejected.
        """
        Student.objects.create(
            school=self.school_a, student_id='2026-0001',
            first_name='Alice', last_name='Dupont',
            gender='F', date_of_birth='2010-01-01',
        )
        with self.assertRaises(IntegrityError):
            Student.objects.create(
                school=self.school_a, student_id='2026-0001',
                first_name='Bob', last_name='Martin',
                gender='M', date_of_birth='2010-01-01',
            )


class MatriculeAutoGenerationTest(TestCase):
    """Requirement 3 — matricules are generated automatically."""

    def setUp(self):
        self.school = _school('École Génération', code='SCH-GEN-01')

    def test_matricule_generated_on_creation(self):
        """Req 6 (test 4): student_id is filled in automatically on save."""
        student = _student(self.school)
        self.assertNotEqual(student.student_id, '')
        self.assertIsNotNone(student.student_id)

    def test_sequential_matricules_are_unique(self):
        """Consecutive students receive different matricules."""
        s1 = _student(self.school, first_name='A')
        s2 = _student(self.school, first_name='B')
        self.assertNotEqual(s1.student_id, s2.student_id)

    def test_matricules_are_sequential(self):
        """Sequence counter increments by 1 each time."""
        config = MatriculeConfig.objects.create(school=self.school, last_sequence=0)
        m1 = config.generate_next()
        m2 = config.generate_next()
        # Default format: YYYY-XXXX
        seq1 = int(m1.split('-')[-1])
        seq2 = int(m2.split('-')[-1])
        self.assertEqual(seq2, seq1 + 1)

    def test_existing_matricule_not_overwritten_on_save(self):
        """Re-saving a student must not change their matricule."""
        student = _student(self.school)
        original = student.student_id
        student.first_name = 'Modifié'
        student.save()
        student.refresh_from_db()
        self.assertEqual(student.student_id, original)


class MatriculeConfigPerSchoolTest(TestCase):
    """Requirement 3 — each school has its own format and independent sequence."""

    def test_each_school_has_independent_sequence(self):
        """
        Req 6 (test 1 & 3): Two schools produce the same sequence numbers
        independently (their counters do not interfere).
        """
        school_a = _school('École Séquence A', code='SCH-SEQ-A')
        school_b = _school('École Séquence B', code='SCH-SEQ-B')
        a1 = _student(school_a, first_name='A1')
        b1 = _student(school_b, first_name='B1')
        # Both start at sequence 1; their student_ids end with the same number
        # but belong to different schools — which is valid.
        a_seq = int(a1.student_id.split('-')[-1])
        b_seq = int(b1.student_id.split('-')[-1])
        self.assertEqual(a_seq, 1)
        self.assertEqual(b_seq, 1)

    def test_custom_prefix_in_matricule(self):
        """A school can configure a custom prefix."""
        school = _school('École Préfixe', code='SCH-PFX-01')
        config = MatriculeConfig.objects.create(
            school=school, prefix='ELV', separator='-',
            include_year=True, num_digits=4, last_sequence=0,
        )
        m = config.generate_next()
        self.assertTrue(m.startswith('ELV-'), f"Expected ELV-* prefix, got '{m}'")

    def test_no_year_in_matricule(self):
        """A school can turn off the year component."""
        school = _school('École Sans Année', code='SCH-NOYR-01')
        config = MatriculeConfig.objects.create(
            school=school, prefix='', separator='-',
            include_year=False, num_digits=4, last_sequence=0,
        )
        m = config.generate_next()
        # Should be just the zero-padded sequence number.
        self.assertEqual(m, '0001')

    def test_custom_digit_count(self):
        """A school can configure the number of digits in the sequence."""
        school = _school('École 6 Chiffres', code='SCH-6DIG-01')
        config = MatriculeConfig.objects.create(
            school=school, prefix='', separator='-',
            include_year=False, num_digits=6, last_sequence=0,
        )
        m = config.generate_next()
        self.assertEqual(m, '000001')


class DataIsolationTest(TestCase):
    """Requirement 5 — a school's data is not visible to another school."""

    def setUp(self):
        self.school_a = _school('École Isolée A', code='SCH-ISO-A')
        self.school_b = _school('École Isolée B', code='SCH-ISO-B')
        _student(self.school_a, first_name='Élève', last_name='A')
        _student(self.school_b, first_name='Élève', last_name='B')

    def test_student_filter_by_school(self):
        """Filtering by school returns only that school's students."""
        students_a = Student.objects.filter(school=self.school_a)
        students_b = Student.objects.filter(school=self.school_b)
        self.assertEqual(students_a.count(), 1)
        self.assertEqual(students_b.count(), 1)
        self.assertNotEqual(students_a.first().school, students_b.first().school)

    def test_students_from_other_school_not_accessible(self):
        """School A's students are not in School B's queryset."""
        students_b = Student.objects.filter(school=self.school_b)
        school_a_ids = Student.objects.filter(school=self.school_a).values_list('pk', flat=True)
        for pk in school_a_ids:
            self.assertFalse(students_b.filter(pk=pk).exists())


class EmailDistinctionTest(TestCase):
    """Requirement 2 — contact email ≠ login email."""

    def test_school_contact_email_not_unique(self):
        """Two schools may share the same contact email."""
        shared_email = 'contact@example.test'
        s1 = School.objects.create(
            name='École Email 1', address='addr', city='city',
            country='CI', email=shared_email,
        )
        # Should not raise — no unique constraint on school.email.
        s2 = School.objects.create(
            name='École Email 2', address='addr', city='city',
            country='CI', email=shared_email,
        )
        self.assertEqual(s1.email, s2.email)

    def test_user_login_email_is_unique(self):
        """Login emails (User.email) are globally unique."""
        from apps.users.models import User
        User.objects.create(
            email='unique@test.local',
            first_name='A', last_name='B',
            role='enseignant',
        )
        with self.assertRaises(IntegrityError):
            User.objects.create(
                email='unique@test.local',
                first_name='C', last_name='D',
                role='enseignant',
            )
