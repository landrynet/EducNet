"""Initial School schema — establishes the baseline before V1.4."""

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='School',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name="Nom de l'établissement")),
                ('code', models.CharField(max_length=20, unique=True, verbose_name='Code')),
                ('school_type', models.CharField(
                    choices=[
                        ('primaire', 'École Primaire'),
                        ('secondaire', 'École Secondaire'),
                        ('lycee', 'Lycée'),
                        ('universite', 'Université'),
                        ('autre', 'Autre'),
                    ],
                    default='secondaire',
                    max_length=20,
                    verbose_name="Type d'établissement",
                )),
                ('address', models.TextField(verbose_name='Adresse')),
                ('city', models.CharField(max_length=100, verbose_name='Ville')),
                ('country', models.CharField(default="Côte d'Ivoire", max_length=100, verbose_name='Pays')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Téléphone')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='Email de contact')),
                ('website', models.URLField(blank=True, verbose_name='Site web')),
                ('logo', models.ImageField(blank=True, null=True, upload_to='schools/logos/', verbose_name='Logo')),
                ('director_name', models.CharField(blank=True, max_length=200, verbose_name='Nom du directeur')),
                ('registration_number', models.CharField(blank=True, max_length=50, verbose_name="Numéro d'agrément")),
                ('founded_year', models.PositiveIntegerField(blank=True, null=True, verbose_name='Année de fondation')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Dernière modification')),
            ],
            options={
                'verbose_name': 'École',
                'verbose_name_plural': 'Écoles',
                'ordering': ['name'],
            },
        ),
    ]
