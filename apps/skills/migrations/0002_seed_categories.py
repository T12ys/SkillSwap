from django.db import migrations
from django.utils.text import slugify

CATEGORIES = [
    'Programming', 'Design', 'Languages', 'Marketing', 'Music',
    'Photography', 'Business', 'Mathematics', 'Other',
]


def create_categories(apps, schema_editor):
    Category = apps.get_model('skills', 'Category')
    for name in CATEGORIES:
        Category.objects.get_or_create(slug=slugify(name), defaults={'name': name})


def delete_categories(apps, schema_editor):
    Category = apps.get_model('skills', 'Category')
    Category.objects.filter(slug__in=[slugify(n) for n in CATEGORIES], offers__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('skills', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_categories, delete_categories),
    ]
