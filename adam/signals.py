from django.db.models import signals
from django.dispatch import receiver
from django.db.models.signals import m2m_changed
from .models import PanelDocument, PanelMaster
from .adam import *
from django.core.exceptions import ValidationError
import os
from django.conf import settings
from django.contrib.gis.geos.point import Point
from datetime import datetime


# post_save method
@receiver(signals.post_save, sender=PanelDocument)
def create_document(sender, instance, created, **kwargs):
    print("Save method is called", kwargs)
    if settings.DATA_FILE_DIR and instance.document:
        excelfile = settings.DATA_FILE_DIR + instance.document.url
        excelfile = excelfile.replace("/", "\\")
        print('\n excel file =======')
        excel_to_csv(excelfile)