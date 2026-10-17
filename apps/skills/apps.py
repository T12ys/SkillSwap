from django.apps import AppConfig
from django.db.backends.signals import connection_created


def python_lower(value):
    if isinstance(value, str):
        return value.lower()
    return value


# sqlite lower for cyrillic
def unicode_lower_for_sqlite(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        connection.connection.create_function('LOWER', 1, python_lower, deterministic=True)


class SkillsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.skills'

    def ready(self):
        connection_created.connect(unicode_lower_for_sqlite)

