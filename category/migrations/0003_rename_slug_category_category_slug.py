# Generated by Django 5.0.3 on 2024-03-28 21:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0002_alter_category_slug'),
    ]

    operations = [
        migrations.RenameField(
            model_name='category',
            old_name='slug',
            new_name='category_slug',
        ),
    ]
