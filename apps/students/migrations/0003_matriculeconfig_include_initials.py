"""V1.5 — Add include_initials to MatriculeConfig.

Adds a boolean flag that, when enabled, inserts the student's initials
(first letter of first name + first letter of last name) into the
auto-generated matricule string.

For databases that already ran 0002: the ALTER TABLE adds the column with
a safe default of False so existing configs are unchanged.
For fresh databases: the column is included from creation via 0001+0002+this.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0002_v14_per_school_matricule'),
    ]

    operations = [
        migrations.AddField(
            model_name='matriculeconfig',
            name='include_initials',
            field=models.BooleanField(
                default=False,
                verbose_name="Inclure les initiales de l'élève",
                help_text='Ajoute la 1ère lettre du prénom et du nom (ex. KJ pour Konan Jean).',
            ),
        ),
    ]
