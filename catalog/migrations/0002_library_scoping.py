import django.db.models.deletion
from django.db import migrations, models


def assign_existing_data(apps, schema_editor):
    """Existing categories/books go to a default library so nothing is lost."""
    Library = apps.get_model('core', 'Library')
    Category = apps.get_model('catalog', 'Category')
    Book = apps.get_model('catalog', 'Book')
    if Category.objects.filter(library__isnull=True).exists() or Book.objects.filter(library__isnull=True).exists():
        lib, _ = Library.objects.get_or_create(code='main', defaults={'name': 'Main Library'})
        Category.objects.filter(library__isnull=True).update(library=lib)
        Book.objects.filter(library__isnull=True).update(library=lib)


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='category', name='library',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name='categories', to='core.library'),
        ),
        migrations.AddField(
            model_name='book', name='library',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name='books', to='core.library'),
        ),
        migrations.RunPython(assign_existing_data, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='category', name='library',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                    related_name='categories', to='core.library'),
        ),
        migrations.AlterField(
            model_name='book', name='library',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                    related_name='books', to='core.library'),
        ),
        migrations.AlterField(
            model_name='category', name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='book', name='isbn',
            field=models.CharField(max_length=20, verbose_name='ISBN'),
        ),
        migrations.AlterUniqueTogether(name='category', unique_together={('library', 'name')}),
        migrations.AlterUniqueTogether(name='book', unique_together={('library', 'isbn')}),
    ]
