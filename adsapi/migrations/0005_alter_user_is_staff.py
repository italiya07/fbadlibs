# Generated by Django 3.2.13 on 2022-06-15 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adsapi', '0004_remove_user_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_staff',
            field=models.BooleanField(default=True),
        ),
    ]
