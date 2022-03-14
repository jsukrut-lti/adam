from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.urls import reverse
from django_object_actions import DjangoObjectActions
from django.core.exceptions import ValidationError
from .calc import excel_to_csv, import_csv_database, prepare_csv_import_journal
from django.shortcuts import redirect
from calc.views import financial_analysis_view
# from calc.forms import JournalMasterAdminForm
### Testing
import os
from calc.models import CurrencyMaster, CurrencyRateMaster, CalculatorMaster, \
    JournalMaster, Profile, Document, ScenarioMaster, RateAnalysis, RateAnalysisDetails, RateAnalysisHistory

# Register your models here.
class CurrencyMasterAdmin(admin.ModelAdmin):
    list_display = ("code", "name",)
    search_fields = ['code','name']

admin.site.register(CurrencyMaster, CurrencyMasterAdmin)

class CurrencyRateMasterAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "conversion_rate",)
    search_fields = ['code','name','from_currency__code','to_currency__code']
    list_filter = ('from_currency','to_currency')

admin.site.register(CurrencyRateMaster, CurrencyRateMasterAdmin)

class CalculatorMasterAdmin(admin.ModelAdmin):
    list_display = ("name","primary_currency_id","active","is_published") # "currency_ids",
    search_fields = ['name','primary_currency_id__code','currency_ids__name']
    list_filter = ('primary_currency_id','currency_ids','active','is_published',)

    def changelist_view(self, request, extra_context=None):
        default_filter = False
        try:
            ref = request.META['HTTP_REFERER']
            pinfo = request.META['PATH_INFO']
            qstr = ref.split(pinfo)
            if len(qstr) < 2:
                default_filter = True
        except:
            default_filter = True
        if default_filter:
            q = request.GET.copy()
            q['active__exact'] = True
            request.GET = q
            request.META['QUERY_STRING'] = request.GET.urlencode()
        return super(CalculatorMasterAdmin, self).changelist_view(request, extra_context=extra_context)

    def save_related(self, request, form, formsets, change):
        super(CalculatorMasterAdmin, self).save_related(request, form, formsets, change)

admin.site.register(CalculatorMaster, CalculatorMasterAdmin)

class JournalMasterAdmin(admin.ModelAdmin):
    list_display = ("code", "name",)
    search_fields = ['code','name','calculator_ids__name']
    list_filter = ('calculator_ids','active')

    def changelist_view(self, request, extra_context=None):
        default_filter = False
        try:
            ref = request.META['HTTP_REFERER']
            pinfo = request.META['PATH_INFO']
            qstr = ref.split(pinfo)
            if len(qstr) < 2:
                default_filter = True
        except:
            default_filter = True
        if default_filter:
            q = request.GET.copy()
            q['active__exact'] = True
            request.GET = q
            request.META['QUERY_STRING'] = request.GET.urlencode()
        return super(JournalMasterAdmin, self).changelist_view(request, extra_context=extra_context)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "calculator_ids":
            kwargs["queryset"] = CalculatorMaster.objects.filter(active=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

admin.site.register(JournalMaster, JournalMasterAdmin)

class profileadmin(admin.ModelAdmin):
    list_display=('user','calculator_id')
    search_fields = ['user__username','calculator_id__name']
    list_filter = ('calculator_id',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "calculator_id":
            kwargs["queryset"] = CalculatorMaster.objects.filter(active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Profile, profileadmin)

class ScenarioAdmin(admin.ModelAdmin):
    list_display = ("name", "description")

admin.site.register(ScenarioMaster, ScenarioAdmin)

class DocumentAdmin(DjangoObjectActions, admin.ModelAdmin):
    fieldsets = ( ('Basic Info', {'fields': ('calculator_id','name','scenario_id', 'document',), 'classes': ['wide']}),)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_readonly_fields(self, request, obj=None):
        # make all fields readonly
        readonly_fields = self.readonly_fields
        if obj:
            readonly_fields = list(
                set([field.name for field in self.opts.local_fields] +
                    [field.name for field in self.opts.local_many_to_many]))
        return readonly_fields

    list_display = ("calculator_id", "name", "scenario_id", "uploaded_at",)
    search_fields = ['calculator_id__name','name','scenario_id__name']
    list_filter = ('calculator_id','scenario_id')

    def change_view(self, request, object_id, extra_context=None):
        ''' customize add/edit form '''
        if object_id:
            extra_context = extra_context or {}
            extra_context['show_save_and_add_another'] = False
            extra_context['show_save_and_continue'] = False
            extra_context['show_save'] = False
            extra_context['show_delete'] = False
        return super(DocumentAdmin, self).change_view(request, object_id, extra_context=extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        doc_obj = Document.objects.values('calculator_id').distinct()
        doc_ref_cal_rec = doc_obj and list(doc_obj) or []
        doc_ref_cal_rec = doc_obj and list(map(lambda x: x.get('calculator_id',False), doc_ref_cal_rec)) or []
        doc_ref_cal_rec = doc_ref_cal_rec and list(filter(lambda x: x != False, doc_ref_cal_rec)) or []
        if db_field.name == "calculator_id":
            filter_obj = False
            filters = {'active': True}
            filter_obj = CalculatorMaster.objects.filter(**filters)
            kwargs["queryset"] = filter_obj
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def export_csv(self, request, obj):
        if settings.DATA_FILE_DIR and obj.document and obj.calculator_id:
            excelfile = settings.DATA_FILE_DIR + obj.document.url
            excelfile = excelfile.replace("/", "\\")
            if excelfile and os.path.exists(excelfile):
                excel_to_csv(excelfile,calculator_directory=obj.calculator_id.directory_name)
                # import_csv_database(calculator_id=obj.calculator_id.id,calculator_directory=obj.calculator_id.directory_name)
                # prepare_csv_import_journal(calculator_id=obj.calculator_id.id,calculator_directory=obj.calculator_id.directory_name)

    def import_journal(self, request, obj):
        if obj.calculator_id:
            import_csv_database(calculator_id=obj.calculator_id.id,calculator_directory=obj.calculator_id.directory_name)
            prepare_csv_import_journal(calculator_id=obj.calculator_id.id,calculator_directory=obj.calculator_id.directory_name)

    change_actions = (
        "export_csv",
        "import_journal",
    )

admin.site.register(Document, DocumentAdmin)

class RateAnalysisDetailsAdminInline(admin.TabularInline):
    model = RateAnalysisDetails

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class RateAnalysisHistoryAdminInline(admin.TabularInline):
    model = RateAnalysisHistory

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class RateAnalysisAdmin(DjangoObjectActions, admin.ModelAdmin):

    fieldsets = (
        ('Basic Info', {'fields': ('rate_analysis_no','scenario_id','document_id','status'), 'classes': ['wide']}),
        ('Metrics Info', {'fields': ('filter_perc','society_approval_rate_perc','avg_price_change_perc',), 'classes': ['form-row-6columns']}),
        ('', {'fields': ('description','remarks',), 'classes': ['form-row-6columns']}),
        ('Log Info', {'fields': ('created_by','modified_by'), 'classes': ['form-row-6columns']}),
    )

    inlines = (RateAnalysisDetailsAdminInline,RateAnalysisHistoryAdminInline,)
    list_display = ("rate_analysis_no","scenario_id","filter_perc","society_approval_rate_perc","avg_price_change_perc","status","remarks")
    search_fields = ['rate_analysis_no','scenario_id__name','status']
    list_filter = ('rate_analysis_no','scenario_id','status')

    def has_add_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        # make all fields readonly
        readonly_fields = self.readonly_fields
        exclude_fileds = ['description','remarks']
        if obj:
            readonly_fields = list(
                set([field.name for field in self.opts.local_fields] +
                    [field.name for field in self.opts.local_many_to_many]))
        diff = set(readonly_fields) - set(exclude_fileds)
        readonly_fields = diff and list(diff) or readonly_fields
        return readonly_fields

    def get_changeform_initial_data(self, request):
        get_data = super(RateAnalysisAdmin, self).get_changeform_initial_data(request)
        get_data['created_by'] = request.user.pk
        return get_data

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        else:
            obj.modified_by = request.user
        obj.save()

    def approve(self, request, obj):
        obj.modified_by = request.user
        obj.status = 'approve'
        obj.save()

    def reject(self, request, obj):
        print('\n fadkfk ====',request)
        print('\n obj ====',obj)
        print('\n self ====',self)
        obj.modified_by = request.user
        obj.status = 'reject'
        obj.save()

    def cancel(self, request, obj):
        obj.modified_by = request.user
        obj.status = 'cancel'
        obj.save()

    def reopen(self, request, obj):
        obj.modified_by = request.user
        obj.status = 'pending'
        obj.save()

    def edit_price(self, request, obj):
        if obj.status == 'pending':
            return_url = '/financial-analysis/rate_analysis_id={}'.format(str(obj.id))
            return redirect(return_url)

    change_actions = (
        "reopen",
        "edit_price",
        "approve",
        "reject",
        "cancel",
    )

admin.site.register(RateAnalysis, RateAnalysisAdmin)
