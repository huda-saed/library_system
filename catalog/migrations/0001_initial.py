import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('author', models.CharField(max_length=150)),
                ('isbn', models.CharField(max_length=20, unique=True, verbose_name='ISBN')),
                ('publisher', models.CharField(blank=True, max_length=150)),
                ('year_published', models.PositiveIntegerField(blank=True, null=True)),
                ('total_copies', models.PositiveIntegerField(default=1)),
                ('available_copies', models.PositiveIntegerField(default=1)),
                ('shelf_location', models.CharField(blank=True, max_length=50)),
                ('cover_image', models.ImageField(blank=True, null=True, upload_to='book_covers/')),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='books', to='catalog.category')),
            ],
            options={
                'ordering': ['title'],
            },
        ),
    ]
