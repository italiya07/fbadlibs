# Generated by Django 3.2.13 on 2022-07-04 06:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adsapi', '0012_saveads'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='paid_until',
            field=models.DateField(blank=True, null=True),
        ),
    ]
