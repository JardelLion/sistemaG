# Generated by Django 5.1.2 on 2024-11-08 13:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_totalproduct_product'),
    ]

    operations = [
        migrations.DeleteModel(
            name='TotalProduct',
        ),
    ]
