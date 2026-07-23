#!/usr/bin/env python
"""
Seed Test Data Script — EduManager V1.1
========================================
Generates a complete, realistic test environment with multiple schools,
users of each role, students, parents, staff, academic data, and finance records.

Usage:
    python seed_test_data.py [--reset]

Options:
    --reset   Delete all existing data before seeding (DANGEROUS — dev only)

IMPORTANT: Never run on production. This script is for development/testing only.
"""

import os
import sys
import django
import argparse
from datetime import date, timedelta
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from apps.users.models import User, Role
from apps.schools.models import School


# ─── Helpers ───────────────────────────────────────────────────────────────

def log(msg, level='INFO'):
    colors = {'INFO': '\033[94m', 'OK': '\033[92m', 'WARN': '\033[93m', 'ERR': '\033[91m'}
    reset = '\033[0m'
    print(f"{colors.get(level, '')}[{level}]{reset} {msg}")


# ─── School Data ────────────────────────────────────────────────────────────

SCHOOLS = [
    {
        'name': 'Lycée Moderne de Cocody',
        'code': 'LMC-001',
        'email': 'lmc@edumanager.test',
        'phone': '+225 27 22 41 00 00',
        'address': 'Cocody, Abidjan',
        'city': 'Abidjan',
        'country': 'Côte d\'Ivoire',
        'school_type': 'public',
    },
    {
        'name': 'Collège Privé Saint-Michel',
        'code': 'CSM-002',
        'email': 'csm@edumanager.test',
        'phone': '+225 27 22 42 00 00',
        'address': 'Plateau, Abidjan',
        'city': 'Abidjan',
        'country': 'Côte d\'Ivoire',
        'school_type': 'private',
    },
]

# ─── User Data per school ───────────────────────────────────────────────────

def create_school_users(school, prefix):
    """Create one user per role for a given school."""
    users_created = []

    role_configs = [
        {
            'email': f'admin.{prefix}@edumanager.test',
            'first_name': 'Admin',
            'last_name': prefix.upper(),
            'role': Role.ADMIN_ECOLE,
            'password': 'Test@2024!',
        },
        {
            'email': f'secretaire.{prefix}@edumanager.test',
            'first_name': 'Marie',
            'last_name': f'Konan {prefix.upper()}',
            'role': Role.SECRETAIRE,
            'password': 'Test@2024!',
        },
        {
            'email': f'enseignant.{prefix}@edumanager.test',
            'first_name': 'Paul',
            'last_name': f'Kouassi {prefix.upper()}',
            'role': Role.ENSEIGNANT,
            'password': 'Test@2024!',
        },
        {
            'email': f'enseignant2.{prefix}@edumanager.test',
            'first_name': 'Aminata',
            'last_name': f'Diallo {prefix.upper()}',
            'role': Role.ENSEIGNANT,
            'password': 'Test@2024!',
        },
        {
            'email': f'comptable.{prefix}@edumanager.test',
            'first_name': 'Jean',
            'last_name': f'Brou {prefix.upper()}',
            'role': Role.COMPTABLE,
            'password': 'Test@2024!',
        },
    ]

    for config in role_configs:
        if User.objects.filter(email=config['email']).exists():
            log(f"  User already exists: {config['email']}", 'WARN')
            continue
        user = User.objects.create_user(
            email=config['email'],
            password=config['password'],
            first_name=config['first_name'],
            last_name=config['last_name'],
            role=config['role'],
            school=school,
            must_change_password=False,
            profile_completed=True,
            is_active=True,
        )
        users_created.append(user)
        log(f"  Created user: {user.get_full_name()} ({user.get_role_display()})", 'OK')
    return users_created


def create_academic_data(school):
    """Create academic years, levels, classrooms, and subjects."""
    try:
        from apps.academic.models import AcademicYear, Level, Classroom, Subject

        # Academic Year
        year, created = AcademicYear.objects.get_or_create(
            school=school,
            name='2024-2025',
            defaults={
                'start_date': date(2024, 9, 1),
                'end_date': date(2025, 6, 30),
                'is_current': True,
            }
        )
        if created:
            log(f"  Academic year created: {year.name}", 'OK')

        # Levels
        level_names = ['6ème', '5ème', '4ème', '3ème', 'Seconde', 'Première', 'Terminale']
        level_objects = []
        for order, level_name in enumerate(level_names):
            level_obj, created = Level.objects.get_or_create(
                school=school,
                name=level_name,
                defaults={'order': order}
            )
            level_objects.append(level_obj)

        # Classrooms
        classrooms = []
        for level_obj in level_objects[:3]:  # Create first 3 classrooms for brevity
            cls, created = Classroom.objects.get_or_create(
                school=school,
                name=f'{level_obj.name} A',
                academic_year=year,
                defaults={'capacity': 35, 'level': level_obj}
            )
            classrooms.append(cls)
            if created:
                log(f"  Classroom created: {cls.name}", 'OK')

        # Subjects
        subject_names = [
            ('Mathématiques', 'MATH'),
            ('Français', 'FR'),
            ('Histoire-Géographie', 'HG'),
            ('Sciences de la Vie et de la Terre', 'SVT'),
            ('Physique-Chimie', 'PC'),
            ('Anglais', 'ANG'),
            ('Éducation Physique et Sportive', 'EPS'),
            ('Philosophie', 'PHILO'),
        ]
        subjects = []
        for name, code in subject_names:
            subj, created = Subject.objects.get_or_create(
                school=school,
                code=f'{code}-{school.code[:3]}',
                defaults={'name': name, 'coefficient': random.randint(1, 5)}
            )
            subjects.append(subj)
            if created:
                log(f"  Subject created: {subj.name}", 'OK')

        return year, classrooms, subjects
    except Exception as e:
        log(f"  Could not create academic data: {e}", 'WARN')
        return None, [], []


def create_students(school, count=15):
    """Create test students for a school."""
    try:
        from apps.students.models import Student

        first_names_m = ['Kouamé', 'Kofi', 'Kwame', 'Ange', 'Yves', 'Jean', 'Marc', 'David', 'Serge', 'Eric']
        first_names_f = ['Aya', 'Fatoumata', 'Aminata', 'Marie', 'Sophie', 'Aïcha', 'Nathalie', 'Grace', 'Patricia', 'Christelle']
        last_names = ['Konan', 'Kouassi', 'Assi', 'Brou', 'Touré', 'Coulibaly', 'Diallo', 'Traoré', 'Ouattara', 'Yao']

        # V1.4: student_id (matricule) is now auto-generated by Student.save().
        created_count = 0
        for i in range(count):
            gender = 'M' if i % 2 == 0 else 'F'
            first_name = random.choice(first_names_m if gender == 'M' else first_names_f)
            last_name = random.choice(last_names)

            Student.objects.create(
                school=school,
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=date(2005 + (i % 5), random.randint(1, 12), random.randint(1, 28)),
                is_active=True,
            )
            created_count += 1

        log(f"  Created {created_count} students", 'OK')
    except Exception as e:
        log(f"  Could not create students: {e}", 'WARN')


def create_staff_profiles(school, teachers):
    """Create staff profiles for teacher users."""
    try:
        from apps.staff.models import StaffProfile
        for user in teachers:
            if not StaffProfile.objects.filter(user=user).exists():
                StaffProfile.objects.create(
                    user=user,
                    school=school,
                    staff_type='teacher',
                    contract_type='permanent',
                    employee_id=f"EMP{school.code[:3]}{user.pk:04d}",
                    hire_date=date(2020, 9, 1),
                    specialization='Mathématiques et Sciences',
                    is_active=True,
                )
                log(f"  Staff profile created for: {user.get_full_name()}", 'OK')
    except Exception as e:
        log(f"  Could not create staff profiles: {e}", 'WARN')


def create_finance_data(school, students):
    """Create sample payment records."""
    try:
        from apps.finance.models import Payment, FeeType
        from apps.users.models import User

        # Fee types
        fee_type, _ = FeeType.objects.get_or_create(
            school=school,
            name='Frais de scolarité',
            defaults={'amount': 150000, 'description': 'Frais annuels de scolarité'}
        )

        accountant = User.objects.filter(school=school, role=Role.COMPTABLE, is_active=True).first()
        if not accountant:
            return

        statuses = ['paid', 'paid', 'paid', 'pending', 'pending', 'overdue']
        created_count = 0
        for i, student in enumerate(students[:10]):
            if Payment.objects.filter(school=school, student=student).exists():
                continue
            status = statuses[i % len(statuses)]
            payment_kwargs = dict(
                school=school,
                student=student,
                fee_type=fee_type,
                amount_due=150000,
                amount=150000 if status == 'paid' else 0,
                status=status,
                method='cash',
                received_by=accountant,
            )
            if status == 'paid':
                payment_kwargs['payment_date'] = date.today() - timedelta(days=random.randint(0, 60))
            Payment.objects.create(**payment_kwargs)
            created_count += 1
        log(f"  Created {created_count} payment records", 'OK')
    except Exception as e:
        log(f"  Could not create finance data: {e}", 'WARN')


# ─── Main ───────────────────────────────────────────────────────────────────

def seed(reset=False):
    log("═══════════════════════════════════════════════")
    log("  EduManager — Seed Test Data V1.1")
    log("═══════════════════════════════════════════════")

    if reset:
        log("RESETTING all school/user data...", 'WARN')
        School.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        log("Reset complete.", 'WARN')

    # ── Super Admin ──────────────────────────────────
    log("\n[1/5] Super Admin...")
    if not User.objects.filter(email='admin@edumanager.local').exists():
        User.objects.create_superuser(
            email='admin@edumanager.local',
            password='Admin@2024!',
            first_name='Super',
            last_name='Admin',
            role=Role.SUPER_ADMIN,
            must_change_password=False,
        )
        log("  Super Admin created", 'OK')
    else:
        log("  Super Admin already exists", 'WARN')

    # ── Schools ──────────────────────────────────────
    log("\n[2/5] Schools...")
    school_objects = []
    for school_data in SCHOOLS:
        school, created = School.objects.get_or_create(
            code=school_data['code'],
            defaults=school_data
        )
        school_objects.append(school)
        if created:
            log(f"  School created: {school.name}", 'OK')
        else:
            log(f"  School already exists: {school.name}", 'WARN')

    # ── Users per school ─────────────────────────────
    log("\n[3/5] School users...")
    all_teachers = {}
    for school, prefix in zip(school_objects, ['lmc', 'csm']):
        log(f"\n  → {school.name}:")
        users = create_school_users(school, prefix)
        teachers = [u for u in users if u.role == Role.ENSEIGNANT]
        if not teachers:
            teachers = list(User.objects.filter(school=school, role=Role.ENSEIGNANT))
        all_teachers[school.pk] = teachers

    # ── Academic + Students ──────────────────────────
    log("\n[4/5] Academic data & students...")
    for school in school_objects:
        log(f"\n  → {school.name}:")
        year, classrooms, subjects = create_academic_data(school)
        create_students(school, count=20)
        create_staff_profiles(school, all_teachers.get(school.pk, []))

    # ── Finance ──────────────────────────────────────
    log("\n[5/5] Finance records...")
    for school in school_objects:
        log(f"\n  → {school.name}:")
        try:
            from apps.students.models import Student
            students = list(Student.objects.filter(school=school))
            create_finance_data(school, students)
        except Exception as e:
            log(f"  {e}", 'WARN')

    # ── Summary ──────────────────────────────────────
    log("\n═══════════════════════════════════════════════")
    log("  SEED COMPLETE — Test Credentials:", 'OK')
    log("═══════════════════════════════════════════════")
    log("  Super Admin:  admin@edumanager.local  / Admin@2024!")
    log("  Admin LMC:    admin.lmc@edumanager.test / Test@2024!")
    log("  Admin CSM:    admin.csm@edumanager.test / Test@2024!")
    log("  Secrétaire:   secretaire.lmc@edumanager.test / Test@2024!")
    log("  Enseignant:   enseignant.lmc@edumanager.test / Test@2024!")
    log("  Comptable:    comptable.lmc@edumanager.test / Test@2024!")
    log("═══════════════════════════════════════════════")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Seed test data for EduManager')
    parser.add_argument('--reset', action='store_true', help='Delete all data before seeding')
    args = parser.parse_args()

    if args.reset:
        confirm = input("WARNING: This will delete ALL data. Type 'CONFIRM' to continue: ")
        if confirm != 'CONFIRM':
            log("Aborted.", 'WARN')
            sys.exit(0)

    seed(reset=args.reset)
