import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_library_scoping'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book', name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name='books', to='catalog.category'),
        ),
    ]
