# Generated by Django 5.1.2 on 2025-01-12 19:12

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('contact', models.CharField(max_length=15)),
                ('address', models.TextField()),
                ('role', models.CharField(choices=[('admin', 'admin'), ('employee', 'employee')], max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('stock_reference', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_stock_reference', to='orders.stockreference')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='employee', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EmployeeHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('contact', models.CharField(max_length=15)),
                ('address', models.TextField()),
                ('role', models.CharField(choices=[('admin', 'admin'), ('employee', 'employee')], max_length=100)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employee_history', to='people.employee')),
                ('stock_reference', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_history_stock_reference', to='orders.stockreference')),
            ],
        ),
        migrations.CreateModel(
            name='LoginActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(max_length=20)),
                ('ip_address', models.GenericIPAddressField()),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
