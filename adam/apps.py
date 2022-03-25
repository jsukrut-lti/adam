from django.apps import AppConfig


class AdamConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'adam'

    def ready(self):
        import adam.signals  # noqa