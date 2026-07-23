"""Initial Student schema — pre-V1.4 baseline with globally unique student_id."""

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('schools', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('school', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='students',
                    to='schools.school',
                )),
                # Pre-V1.4: globally unique — will be relaxed in 0002.
                ('student_id', models.CharField(max_length=20, unique=True, verbose_name='Matricule')),
                ('first_name', models.CharField(max_length=100, verbose_name='Prénom')),
                ('last_name', models.CharField(max_length=100, verbose_name='Nom')),
                ('gender', models.CharField(
                    choices=[('M', 'Masculin'), ('F', 'Féminin')],
                    max_length=1,
                    verbose_name='Genre',
                )),
                ('date_of_birth', models.DateField(verbose_name='Date de naissance')),
                ('place_of_birth', models.CharField(blank=True, max_length=100, verbose_name='Lieu de naissance')),
                ('nationality', models.CharField(default='Ivoirienne', max_length=50, verbose_name='Nationalité')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='students/photos/')),
                ('address', models.TextField(blank=True, verbose_name='Adresse')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Téléphone')),
                ('email', models.EmailField(blank=True, verbose_name='Email')),
                ('previous_school', models.CharField(blank=True, max_length=200, verbose_name='École précédente')),
                ('medical_notes', models.TextField(blank=True, verbose_name='Notes médicales')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('registered_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date d'enregistrement")),
            ],
            options={
                'verbose_name': 'Élève',
                'verbose_name_plural': 'Élèves',
                'ordering': ['last_name', 'first_name'],
            },
        ),
    ]
