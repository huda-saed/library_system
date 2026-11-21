import django.db.models.deletion
from django.db import migrations, models


def assign_existing_users(apps, schema_editor):
    """Existing non-superuser accounts go to a default library so nothing is lost."""
    User = apps.get_model('accounts', 'User')
    Library = apps.get_model('core', 'Library')
    orphans = User.objects.filter(library__isnull=True, is_superuser=False)
    if orphans.exists():
        lib, _ = Library.objects.get_or_create(code='main', defaults={'name': 'Main Library'})
        orphans.update(library=lib)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='library',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='users', to='core.library',
                help_text='The library this user belongs to. Leave empty only for the system owner (superuser).',
            ),
        ),
        migrations.RunPython(assign_existing_users, migrations.RunPython.noop),
    ]
