# Generated by Django 4.0 on 2021-12-28 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('categorytags', '0002_alter_interest_name_alter_skill_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='offertag',
            name='name',
            field=models.CharField(max_length=200, unique=True),
        ),
    ]
