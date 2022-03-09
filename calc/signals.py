from django.db.models import signals
from django.dispatch import receiver
from django.db.models.signals import m2m_changed
from .models import CalculatorMaster, Document
from django.core.exceptions import ValidationError
import os
from django.conf import settings
from datetime import datetime
from .calc import *

# pre_save method signal
@receiver(signals.pre_save, sender=CalculatorMaster)
def create_directory_name(sender, instance, **kwargs):
    name = instance.name.strip()
    instance.directory_name = name.replace(" ", "_")

@receiver(m2m_changed, sender=CalculatorMaster.currency_ids.through)
def prevent_duplicate_secondary_currency(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'pre_add':
        primary_currency_id = []
        if (instance.primary_currency_id and instance.primary_currency_id.id or False) and list(pk_set):
            if instance.primary_currency_id.id in list(pk_set):
                msg = "Primary Currency should not be in Secondary Currencies"
                print(msg)
                # raise ValidationError("my error message")

# pre_save method signal
@receiver(signals.pre_save, sender=Document)
def create_directory_name(sender, instance, **kwargs):
    name = instance.name.strip()
    instance.directory_name = name.replace(" ", "_")

# post_save method
@receiver(signals.post_save, sender=Document)
def create_document(sender, instance, created, **kwargs):
    print("Save method is called",kwargs)
    # if settings.DATA_FILE_DIR and instance.document and instance.calculator_id:
    #     excelfile = settings.DATA_FILE_DIR + instance.document.url
    #     excelfile = excelfile.replace("/", "\\")
    #     print ('\n excel file =======')
        # excel_to_csv(excelfile,calculator_directory=instance.calculator_id.directory_name)
        # import_csv_database(calculator_id=instance.calculator_id.id,calculator_directory=instance.calculator_id.directory_name)
        # prepare_csv_import_journal(calculator_id=instance.calculator_id.id,calculator_directory=instance.calculator_id.directory_name)
