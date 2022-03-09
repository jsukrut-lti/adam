from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

class CalcConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calc'
    verbose_name = "Configuration"

    def ready(self):
        import calc.signals  # noqa
