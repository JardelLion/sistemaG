# Generated by Django 5.1.1 on 2024-10-11 15:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_alter_employee_role'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stockmanager',
            old_name='responsible_user',
            new_name='responsible_user_id',
        ),
    ]
