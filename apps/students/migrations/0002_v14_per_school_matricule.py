"""V1.4 — Switch student_id from globally unique to per-school unique.

For fresh databases: 0001 creates the old schema, this migration updates it.
For existing syncdb databases: run with --fake-initial so that 0001 is skipped
(table already exists) and this migration runs to ALTER the live schema.

Changes applied:
  1. Create MatriculeConfig (per-school matricule format + sequence counter).
  2. Alter student_id: remove global unique, widen max_length 20→30, allow blank
     for auto-generation on first save.
  3. Add UNIQUE(school_id, student_id) constraint.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0001_initial'),
        ('schools', '0001_initial'),
    ]

    operations = [
        # ── 1. Create the MatriculeConfig table ───────────────────────────────
        migrations.CreateModel(
            name='MatriculeConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('school', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='matricule_config',
                    to='schools.school',
                    verbose_name='École',
                )),
                ('prefix', models.CharField(
                    blank=True, default='', max_length=10,
                    verbose_name='Préfixe (ex. ELV)',
                    help_text='Laissez vide pour ne pas utiliser de préfixe.',
                )),
                ('include_year', models.BooleanField(default=True, verbose_name="Inclure l'année")),
                ('separator', models.CharField(default='-', max_length=3, verbose_name='Séparateur')),
                ('num_digits', models.PositiveSmallIntegerField(
                    default=4,
                    verbose_name='Nombre de chiffres',
                    help_text='Nombre de zéros pour rembourrer le numéro séquentiel.',
                )),
                ('last_sequence', models.PositiveIntegerField(default=0, verbose_name='Dernier numéro de séquence')),
            ],
            options={
                'verbose_name': 'Configuration matricule',
                'verbose_name_plural': 'Configurations matricule',
            },
        ),

        # ── 2. Relax student_id: remove global unique, widen field, allow blank ─
        migrations.AlterField(
            model_name='student',
            name='student_id',
            field=models.CharField(
                blank=True,
                max_length=30,
                verbose_name='Matricule',
            ),
        ),

        # ── 3. Add per-school unique constraint ───────────────────────────────
        migrations.AddConstraint(
            model_name='student',
            constraint=models.UniqueConstraint(
                fields=['school', 'student_id'],
                name='unique_student_id_per_school',
            ),
        ),
    ]
