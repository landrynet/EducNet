from django.test import TestCase
from django.urls import reverse

from apps.users.models import Role, User
from .models import School


class SchoolOnboardingTests(TestCase):
    def setUp(self):
        self.super_admin = User.objects.create_superuser(
            email='platform@example.test',
            password='Platform!123',
            first_name='Platform',
            last_name='Admin',
        )
        self.client.force_login(self.super_admin)
        self.school_data = {
            'name': 'École de test',
            # V1.4: code is auto-generated — no longer submitted via the form.
            'school_type': 'secondaire',
            'address': '1 rue du Test',
            'city': 'Abidjan',
            'country': "Côte d'Ivoire",
            'phone': '0700000000',
            'email': 'responsable@example.test',
            'website': '',
            'registration_number': '',
            'founded_year': '',
        }

    def test_school_creation_creates_one_temporary_admin_and_shows_credentials_once(self):
        response = self.client.post(reverse('schools:create'), self.school_data)
        # V1.4: code is auto-generated — look up the school by its name instead.
        school = School.objects.get(name='École de test')
        admin = User.objects.get(school=school, role=Role.ADMIN_ECOLE)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('schools:credentials', args=[school.pk]))
        self.assertTrue(admin.must_change_password)
        self.assertFalse(admin.profile_completed)
        self.assertEqual(admin.email, self.school_data['email'])

        page = self.client.get(response.url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Identifiant')
        self.assertContains(page, 'Mot de passe temporaire')
        self.assertRedirects(
            self.client.get(reverse('schools:credentials', args=[school.pk])),
            reverse('schools:detail', args=[school.pk]),
        )

    def test_first_login_requires_password_change_then_setup(self):
        school = School.objects.create(
            name='École connexion',
            code='TEST-LOGIN',
            school_type='secondaire',
            address='Adresse',
            city='Abidjan',
        )
        admin = User.objects.create(
            email='login@example.test',
            first_name='Admin',
            last_name='Test',
            role=Role.ADMIN_ECOLE,
            school=school,
            must_change_password=True,
            profile_completed=False,
        )
        temporary = 'Temporary!987'
        admin.set_password(temporary)
        admin.save()

        self.client.logout()
        response = self.client.post(reverse('authentication:login'), {
            'username': admin.email,
            'password': temporary,
        })
        self.assertRedirects(response, reverse('authentication:change_password'))

        response = self.client.post(reverse('authentication:change_password'), {
            'temporary_password': temporary,
            'new_password1': 'Zebra!4829Qx',
            'new_password2': 'Zebra!4829Qx',
        })
        self.assertRedirects(response, reverse('authentication:setup'))
        admin.refresh_from_db()
        self.assertFalse(admin.must_change_password)
        self.assertFalse(admin.check_password(temporary))
        self.assertTrue(admin.check_password('Zebra!4829Qx'))

        self.assertRedirects(
            self.client.get(reverse('dashboard:index')),
            reverse('authentication:setup'),
        )

    def test_password_change_requires_the_temporary_password(self):
        school = School.objects.create(
            name='École mot de passe',
            code='TEST-PASSWORD',
            address='Adresse',
            city='Abidjan',
        )
        admin = User.objects.create(
            email='password@example.test',
            first_name='Admin',
            last_name='Test',
            role=Role.ADMIN_ECOLE,
            school=school,
            must_change_password=True,
            profile_completed=False,
        )
        temporary = 'Temporary!456'
        admin.set_password(temporary)
        admin.save()

        self.client.logout()
        self.client.post(reverse('authentication:login'), {
            'username': admin.email,
            'password': temporary,
        })

        response = self.client.post(reverse('authentication:change_password'), {
            'temporary_password': 'wrong-temporary',
            'new_password1': 'Zebra!4829Qx',
            'new_password2': 'Zebra!4829Qx',
        })
        self.assertEqual(response.status_code, 200)
        admin.refresh_from_db()
        self.assertTrue(admin.must_change_password)
        self.assertTrue(admin.check_password(temporary))
        self.assertEqual(
            response.context['form'].errors['temporary_password'][0],
            'Le mot de passe temporaire est incorrect ou a déjà été invalidé.',
        )

    def test_super_admin_school_view_does_not_expose_temporary_credentials(self):
        school = School.objects.create(
            name='École visibilité',
            code='TEST-VISIBILITY',
            email='contact@visibilite.example',
            address='Adresse',
            city='Abidjan',
        )
        admin = User.objects.create(
            email='login@visibilite.example',
            first_name='Responsable',
            last_name='École',
            role=Role.ADMIN_ECOLE,
            school=school,
            must_change_password=True,
        )
        admin.set_password('Temporary!789')
        admin.save()

        response = self.client.get(reverse('schools:detail', args=[school.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, school.email)
        self.assertNotContains(response, 'Temporary!789')
        self.assertNotContains(response, admin.password)

        users_page = self.client.get(reverse('users:list'))
        self.assertEqual(users_page.status_code, 200)
        self.assertNotContains(users_page, admin.email)