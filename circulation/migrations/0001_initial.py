import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BorrowRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('borrow_date', models.DateField(default=django.utils.timezone.localdate)),
                ('due_date', models.DateField()),
                ('return_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('BORROWED', 'Borrowed'), ('RETURNED', 'Returned'), ('OVERDUE', 'Overdue')], default='BORROWED', max_length=10)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='borrow_records', to='catalog.book')),
                ('librarian', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='issued_records', to=settings.AUTH_USER_MODEL)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='borrow_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-borrow_date'],
            },
        ),
        migrations.CreateModel(
            name='Fine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=8)),
                ('payment_status', models.CharField(choices=[('UNPAID', 'Unpaid'), ('PAID', 'Paid')], default='UNPAID', max_length=10)),
                ('payment_date', models.DateField(blank=True, null=True)),
                ('borrow_record', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='fine', to='circulation.borrowrecord')),
            ],
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reservation_date', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('FULFILLED', 'Fulfilled'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=10)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='catalog.book')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-reservation_date'],
            },
        ),
    ]
