# Generated by Django 5.1.1 on 2024-10-11 15:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_rename_responsible_user_stockmanager_responsible_user_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stockmanager',
            old_name='responsible_user_id',
            new_name='responsible_user',
        ),
    ]
