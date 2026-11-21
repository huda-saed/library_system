from django.db import migrations


def create_default_library(apps, schema_editor):
    """Make sure at least one library exists, so the system is usable right away,
    and attach any non-superuser account that has no library yet."""
    Library = apps.get_model('core', 'Library')
    User = apps.get_model('accounts', 'User')
    lib = Library.objects.order_by('id').first()
    if lib is None:
        lib = Library.objects.create(code='main', name='Main Library')
    User.objects.filter(library__isnull=True, is_superuser=False).update(library=lib)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('accounts', '0002_user_library'),
    ]

    operations = [
        migrations.RunPython(create_default_library, migrations.RunPython.noop),
    ]
