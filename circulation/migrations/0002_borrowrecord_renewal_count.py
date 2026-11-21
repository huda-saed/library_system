from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('circulation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='borrowrecord',
            name='renewal_count',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
