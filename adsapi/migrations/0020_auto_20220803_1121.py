# Generated by Django 3.2.13 on 2022-08-03 05:51

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('adsapi', '0019_auto_20220801_1431'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription_details',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='EmailActivation',
        ),
    ]