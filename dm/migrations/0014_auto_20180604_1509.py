# Generated by Django 2.0.6 on 2018-06-04 13:09

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dm', '0013_auto_20180604_1453'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otreeinstance',
            name='name',
            field=models.CharField(max_length=32, validators=[django.core.validators.RegexValidator(code='invalid', message='name is not suitable', regex='^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\\-]*[a-zA-Z0-9])\\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\\-]*[A-Za-z0-9])$')]),
        ),
    ]
