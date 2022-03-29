from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import datetime
import os
from django.db.models import signals
from django.dispatch import receiver
from django.db.models.signals import post_save, post_init
from six import text_type
import dictdiffer

class CurrencyMaster(models.Model):
    code = models.CharField(max_length=10, verbose_name=u"Currency Code", help_text=u"Currency Code", unique=True, blank=True)
    name = models.CharField(max_length=100, verbose_name=u"Currency Name", help_text=u"Currency Name", unique=True, blank=True)

    def __str__(self):
         return self.code

    class Meta:
        db_table = 'currency_master'
        verbose_name_plural = '     Currency Master'

class CurrencyRateMaster(models.Model):
    code = models.CharField(max_length=10, verbose_name=u"Conversion Code", editable=False,  help_text=u"Conversion Code", unique=True, blank=True)
    name = models.CharField(max_length=100, verbose_name=u"Conversion Name", help_text=u"Conversion Name", unique=True, blank=True)
    from_currency = models.ForeignKey(CurrencyMaster, verbose_name=u"From Currency", on_delete=models.CASCADE, related_name='from_currency')
    to_currency = models.ForeignKey(CurrencyMaster, verbose_name=u"To Currency", on_delete=models.CASCADE, related_name='to_currency')
    effective_date = models.DateField(verbose_name=u"Effective Date")
    conversion_rate = models.FloatField(verbose_name=u"Conversion Rate")
    active = models.BooleanField(verbose_name=u"Active", default=True)

    def __str__(self):
        return "%s | %s" % (self.code, self.name)

    class Meta:
        db_table = 'currency_rate_master'
        ordering = ['-effective_date', 'name']
        verbose_name_plural = '    Currency Rate Master'

    def clean(self):
        self.is_cleaned = True
        if self.from_currency or self.to_currency:
            if self.from_currency == self.to_currency:
                raise ValidationError("From Currency and To Currency should not be same")
        super(CurrencyRateMaster, self).clean()

def increment_calculator_seq_no():
    last_calculator_seq = CalculatorMaster.objects.all().order_by('id').last()
    if not last_calculator_seq:
        return 'CAL' + str(datetime.date.today().year) + str(datetime.date.today().month).zfill(2) + '0000'
    calculator_seq_no = last_calculator_seq.calculator_seq_no
    calculator_seq_int = int(calculator_seq_no[9:13])
    new_calculator_seq_int = calculator_seq_int + 1
    new_calculator_seq_no = 'CAL' + str(str(datetime.date.today().year)) + str(datetime.date.today().month).zfill(
        2) + str(new_calculator_seq_int).zfill(4)
    return new_calculator_seq_no

class CalculatorMaster(models.Model):
    name = models.CharField(max_length=100, verbose_name=u"Name", unique=True)
    directory_name = models.CharField(max_length=100, verbose_name=u"Directory", editable=False, unique=True) #
    calculator_seq_no = models.CharField(max_length=20, default=increment_calculator_seq_no, editable=False)
    primary_currency_id = models.ForeignKey(CurrencyMaster, verbose_name=u"Primary Currency", on_delete=models.CASCADE, related_name='primary_currency_id')
    currency_ids = models.ManyToManyField(CurrencyMaster, verbose_name=u"Secondary Currency", related_name="currency_ids", blank=True)
    active = models.BooleanField(verbose_name=u"Active", editable=False, default=True)
    is_published = models.BooleanField(verbose_name=u"Is Published", editable=False, default=False)

    def currency_ids_(self):
        return ', '.join([t.name for t in self.currency_ids.all()])

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'calculator_master'
        verbose_name_plural = '   Calculator Master'
        ordering = ['id']

class JournalMaster(models.Model):
    code = models.CharField(max_length=10, verbose_name=u"Journal Code", unique=True)
    name = models.CharField(max_length=100, verbose_name=u"Journal Name")
    calculator_ids = models.ManyToManyField(CalculatorMaster, verbose_name=u"Tag Calculator")
    active = models.BooleanField(verbose_name=u"Active",default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
         return self.code

    class Meta:
        db_table = 'journal_master'
        verbose_name_plural = '  Journal Master'

class CommonInfo(models.Model):
    journal_code = models.CharField(max_length=10)
    journal_name = models.CharField(max_length=100)
    currency_ids = models.ManyToManyField('Currency', related_name='currency')

    class Meta:
        abstract = True

def get_upload_to(instance, filename):
    directory_name = None
    custom_date = datetime.date.today().strftime('%Y.%m.%d')
    if isinstance(instance, str):
        directory_name = instance
    else:
        directory_name = instance.calculator_id.directory_name
    if filename:
        return os.path.join(custom_date, directory_name, filename)
    return os.path.join(custom_date, directory_name)

class ScenarioMaster(models.Model):
    name = models.CharField(max_length=100, verbose_name=u"Scenario Name", help_text=u"Scenario Name", unique=True, blank=True)
    description = models.TextField(verbose_name=u"Description", help_text=u"Description", null=True, blank=True)

    def __str__(self):
         return self.name

    class Meta:
        db_table = 'scenario_master'
        verbose_name_plural = '     Scenario Master'

class Document(models.Model):

    STATUS = [
    ('draft','Draft'),
    ('export_csv','Export CSV'),
    ('import_journal','Import Journal'),
    ]

    name = models.CharField(max_length=255, verbose_name=u"Description", blank=True)
    uploaded_at = models.DateTimeField(verbose_name=u"Uploaded at",auto_now_add=True)
    document = models.FileField(verbose_name=u"Document", upload_to=get_upload_to)
    calculator_id = models.ForeignKey(CalculatorMaster, verbose_name=u"Tag Calculator", on_delete=models.CASCADE, related_name='calc_id')
    scenario_id = models.ForeignKey(ScenarioMaster, on_delete=models.CASCADE, related_name='scenario_id',
                                    verbose_name=u"Tag Scenario", null=True, blank=True)
    is_auto = models.BooleanField(verbose_name=u"Is Auto", editable=False, default=False)
    status = models.CharField(max_length=20, verbose_name=u"Status", choices=STATUS, default='draft', null=True, blank=True)


    def __str__(self):
        return self.name

    class Meta:
        db_table = 'document_master'
        verbose_name_plural = ' Document'

    def get_file_name(self):
        base = os.path.basename(str(self.document))
        os.path.splitext(base)
        return '{}{}'.format(os.path.splitext(base)[0], os.path.splitext(base)[1])

    def clean(self):
        self.is_cleaned = True
        if False:
            raise ValidationError("Something went wrong!")
        super(Document, self).clean()

class Profile(models.Model):
    profileid = models.AutoField(primary_key=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE, verbose_name=u"User")
    calculator_id = models.ForeignKey(CalculatorMaster,on_delete=models.CASCADE, related_name='calculator_id', verbose_name=u"Tag Calculator", null=True, blank=True)

    def __str__(self):
        return str(self.profileid)

    class Meta:
        verbose_name_plural = '      Profile'

    def clean(self):
        self.is_cleaned = True
        if not self.user.is_superuser:
            if not self.calculator_id:
                raise ValidationError("Calculator is missing")
        super(Profile, self).clean()

def increment_rate_analysis_number():
    last_rate_analysis = RateAnalysis.objects.all().order_by('id').last()
    if not last_rate_analysis:
        return 'RAL' + str(datetime.date.today().year) + str(datetime.date.today().month).zfill(2) + '0000'
    rate_analysis_no = last_rate_analysis.rate_analysis_no
    rate_analysis_int = int(rate_analysis_no[9:13])
    new_rate_analysis_int = rate_analysis_int + 1
    new_rate_analysis_no = 'RAL' + str(str(datetime.date.today().year)) + str(datetime.date.today().month).zfill(2) + str(new_rate_analysis_int).zfill(4)
    return new_rate_analysis_no

class RateAnalysisAbstract(models.Model):

    STATUS = [
    ('pending','Pending for Approval'),
    ('approve','Approved'),
    ('reject','Rejected'),
    ('cancel','Cancelled'),
    ]

    filter_perc = models.FloatField(verbose_name=u"Filter Percentage", null=True, blank=True)
    society_approval_rate_perc = models.FloatField(verbose_name=u"Society Approval Rate (%)", null=True, blank=True)
    avg_price_change_perc = models.FloatField(verbose_name=u"Average Price Change (%)", null=True, blank=True)
    status = models.CharField(max_length=20, verbose_name=u"Status", choices=STATUS, default=None, null=True, blank=True)
    remarks = models.TextField(verbose_name=u"Approve/Reject Remarks", null=True, blank=True)
    description = models.TextField(verbose_name=u"Description", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=u"Created by", null=True, blank=True)

    class Meta:
        abstract = True

    def status_verbose(self):
        if self.status:
            return dict(self.STATUS)[self.status]
        return ''

class RateAnalysis(RateAnalysisAbstract):

    rate_analysis_no = models.CharField(max_length=20, default=increment_rate_analysis_number, editable=False)
    calculator_id = models.ForeignKey(CalculatorMaster, verbose_name=u"Calculator", on_delete=models.CASCADE,related_name='rate_analysis_calculator_id', null=True, blank=True)
    scenario_id = models.ForeignKey(ScenarioMaster, verbose_name=u"Scenario", on_delete=models.CASCADE,related_name='rate_analysis_scenario_id', null=True, blank=True)
    document_id = models.ForeignKey(Document, verbose_name=u"Reference Document", on_delete=models.CASCADE,
                                    related_name='rate_analysis_document_id', null=True, blank=True)
    user_id = models.ForeignKey(User,on_delete=models.CASCADE,related_name='rate_analysis_user_id', null=True, blank=True)
    modified_by = models.ForeignKey(User,on_delete=models.CASCADE, verbose_name=u"Last Edited by", related_name='user_modified_by', null=True, blank=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
         return self.rate_analysis_no

    def __get_label(self, field):
        return text_type(self._meta.get_field(field).verbose_name)

    class Meta:
        db_table = 'calc_rate_analysis'
        verbose_name_plural = '     Rate Analysis'

    def save(self, *args, **kwargs):
        print('rate save .....')
        # Prep the data
        data = {'filter_perc' : 0.00,
                'society_approval_rate_perc' : 0.00,
                'avg_price_change_perc' : 0.00,
                'action' : 'modify',
                'status' : None,
                'remarks' : '',
                'description' : '',
                'created_by': None,
                'modified_by': None,
                'rate_analysis_id': None,
                }
        filtered_diff_data = False
        old_instance = False
        new_instance = False
        if self.id:
            old_instance = RateAnalysis.objects.filter(id=self.id). \
                values('filter_perc', 'society_approval_rate_perc', 'avg_price_change_perc',
                       'status', 'remarks', 'description')
            old_instance_rec = old_instance and old_instance[0] or False
            if old_instance_rec:
                old_data = old_instance_rec
        obj = super(RateAnalysis, self).save(*args, **kwargs)
        new_instance = RateAnalysis.objects.filter(id=self.id).\
            values('filter_perc', 'society_approval_rate_perc', 'avg_price_change_perc',
                   'status', 'remarks', 'description','id', 'modified_by')
        if (old_instance and new_instance):
            diff = list(dictdiffer.diff(old_instance[0], new_instance[0]))
            filtered_diff = diff and list(filter(lambda x: x[0] == 'change', diff)) or []
            filtered_diff = filtered_diff and list(map(lambda x: (x[1], x[2][0]), filtered_diff)) or []
            if filtered_diff:
                if filtered_diff != [()]:
                    filtered_diff_data = filtered_diff and dict(filtered_diff) or []
                    filtered_diff_data = old_instance[0]  ## Assign old data to history
        if filtered_diff_data:
            data['rate_analysis_id'] = self
            data['created_by'] = self.modified_by
            data.update(filtered_diff_data)
            modified_data = list(map(lambda x: data.pop(x,None), ['modified_by']))
            history_rec = RateAnalysisHistory.objects.create(**data)
        return obj

class RateAnalysisDetails(models.Model):

    rate_analysis_id = models.ForeignKey(RateAnalysis, verbose_name=u"Analysis", on_delete=models.CASCADE,related_name='rate_analysis_line_id', null=True, blank=True)
    ownership_structure = models.CharField(max_length=100,verbose_name=u"Ownership Structure", null=True, blank=True)
    apc_change_perc = models.CharField(max_length=10,verbose_name=u"APC Change (%)", null=True, blank=True)
    journal_count = models.FloatField(verbose_name=u"Number of Journal", null=True, blank=True)
    revenue_change = models.FloatField(verbose_name=u"Revenue Change", null=True, blank=True)

    def __str__(self):
         return self.ownership_structure

    class Meta:
        db_table = 'calc_rate_analysis_line'
        verbose_name_plural = '     Rate Analysis Details'

class RateAnalysisHistory(RateAnalysisAbstract):

    ACTIONS = [('modify','Modified')]

    action = models.CharField(max_length=20, verbose_name=u"Action", choices=ACTIONS, null=True,blank=True)
    rate_analysis_id = models.ForeignKey(RateAnalysis, verbose_name=u"Analysis", on_delete=models.CASCADE,related_name='history_analysis_id', null=True, blank=True)

    class Meta:
        db_table = 'calc_rate_analysis_history'
        verbose_name_plural = '     Rate Analysis History'

    def action_verbose(self):
        return dict(self.ACTIONS)[self.action]