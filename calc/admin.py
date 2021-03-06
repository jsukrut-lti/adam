from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.urls import reverse
from django_object_actions import DjangoObjectActions
from django.core.exceptions import ValidationError
from .calc import excel_to_csv, import_csv_database, prepare_csv_import_journal, create_sample_file
from django.shortcuts import redirect
from django.db.models import F
from django.contrib import messages
from calc.views import financial_analysis_view
from django.utils.html import format_html
from urllib.parse import quote, urlparse, parse_qs
# from calc.forms import JournalMasterAdminForm

import os
from calc.models import CurrencyMaster, CurrencyRateMaster, CalculatorMaster, \
    JournalMaster, Profile, Document, ScenarioMaster, RateAnalysis, RateAnalysisDetails, RateAnalysisHistory


# Register your models here.
class CurrencyMasterAdmin(admin.ModelAdmin):
    list_display = ("code", "name",)
    search_fields = ['code', 'name']


admin.site.register(CurrencyMaster, CurrencyMasterAdmin)


class CurrencyRateMasterAdmin(admin.ModelAdmin):
    readonly_fields = ['code']
    list_display = ("code", "name", "effective_date", "conversion_rate","active",)
    search_fields = ['code', 'name', 'from_currency__code', 'to_currency__code']
    list_filter = ('from_currency', 'to_currency', 'active')

    fieldsets = (('',
                  {'fields': ('name', 'from_currency', 'to_currency', 'effective_date', 'conversion_rate', 'active'),
                   'classes': ['wide']}),)


admin.site.register(CurrencyRateMaster, CurrencyRateMasterAdmin)


class CalculatorMasterAdmin(DjangoObjectActions, admin.ModelAdmin):
    fieldsets = (('', {'fields': ('name', 'primary_currency_id', 'currency_ids',), 'classes': ['wide']}),)

    list_display = ("name", "primary_currency_id", "seconday_Currency", "active", "is_published", "button_actions")
    search_fields = ['name', 'primary_currency_id__code', 'currency_ids__name']
    list_filter = ('primary_currency_id', 'currency_ids', 'active', 'is_published',)
    readonly_fields = ['active', 'is_published']
    change_form_template = "calc/admin/admin_calculator_change_form.html"

    def toggle_status(self, request, obj):
        absolute_url_reference = request.build_absolute_uri()
        parsed = urlparse(absolute_url_reference)
        next_url = False
        if parsed.query:
            parsed_dict = parse_qs(parsed.query)
            if parsed_dict.get('next', False):
                next_url = parse_qs(parsed.query)['next'][0]
        print('next_url ===', next_url)
        try:
            msg_status = ''
            if obj.active:
                obj.active = False
                obj.is_published = False
                msg_status = 'de-activated'
            else:
                obj.active = True
                msg_status = 'activated'
            msg = '{} application has been successfully {}'.format(obj.name.title(), msg_status)
            self.message_user(request, msg, level=messages.INFO)
            obj.save()
        except Exception as e:
            print('\n Exception args ... ', e.args)
            self.message_user(request, "Something went wrong. Please try back after later",
                              level=messages.ERROR)
        if next_url:
            return HttpResponseRedirect(next_url)

    def toggle_publish(self, request, obj):
        absolute_url_reference = request.build_absolute_uri()
        parsed = urlparse(absolute_url_reference)
        next_url = False
        if parsed.query:
            parsed_dict = parse_qs(parsed.query)
            if parsed_dict.get('next', False):
                next_url = parse_qs(parsed.query)['next'][0]
        print('next_url ===', next_url)
        try:
            msg_status = ''
            if obj.active:
                if obj.is_published:
                    obj.is_published = False
                    msg_status = 'unpublished'
                else:
                    obj.is_published = True
                    msg_status = 'published'
                obj.save()
                msg = '{} application has been successfully {}'.format(obj.name.title(), msg_status)
                self.message_user(request, msg, level=messages.INFO)
        except Exception as e:
            print('\n Exception args ... ', e.args)
            self.message_user(request, "Something went wrong. Please try back after later",
                              level=messages.ERROR)
        if next_url:
            return HttpResponseRedirect(next_url)

    change_actions = (
        "toggle_status",
        "toggle_publish",
    )

    def get_queryset(self, request):
        self.reference_path = request.path
        return super().get_queryset(request)

    def button_actions(self, obj):
        final_html = '<p> </p>'
        active_href_link = '{}{}{}{}'.format(self.reference_path, obj.id, '/actions/toggle_status/?next=',
                                             self.reference_path)
        active_html_ref = '<a href="{}" title="" class="grp-button">{}</a>&nbsp;'.format(active_href_link,
                                                                                         'Toggle Status')
        publish_html_ref = ''
        if obj.active:
            publish_href_link = '{}{}{}{}'.format(self.reference_path, obj.id, '/actions/toggle_publish/?next=',
                                                  self.reference_path)
            publish_html_ref = '<a href="{}" title="" class="grp-button">{}</a>&nbsp;'.format(publish_href_link,
                                                                                              'Toggle Publish')
        final_html = '{}{}'.format(active_html_ref, publish_html_ref)
        if not final_html:
            final_html = '<p> No pending actions </p>'
        return format_html(final_html)

    button_actions.short_description = 'Button Actions'
    button_actions.allow_tags = True

    def seconday_Currency(self, obj):
        return ", ".join([str(p) for p in obj.currency_ids.all()])

    def save_related(self, request, form, formsets, change):
        super(CalculatorMasterAdmin, self).save_related(request, form, formsets, change)


admin.site.register(CalculatorMaster, CalculatorMasterAdmin)


class JournalMasterAdmin(admin.ModelAdmin):
    list_display = ("code", "name",)
    search_fields = ['code', 'name', 'calculator_ids__name']
    list_filter = ('calculator_ids', 'active')

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
    list_display = ('user', 'calculator_id')
    search_fields = ['user__username', 'calculator_id__name']
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
    fieldsets = (('Basic Info', {'fields': ('calculator_id', 'name', 'document',), 'classes': ['wide']}),)

    change_form_template = "calc/admin/admin_document_change_form.html"

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

    list_display = ("calculator_id", "name", "uploaded_at", "button_actions",)
    search_fields = ['calculator_id__name', 'name']
    list_filter = ('calculator_id',)

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
        doc_ref_cal_rec = doc_obj and list(map(lambda x: x.get('calculator_id', False), doc_ref_cal_rec)) or []
        doc_ref_cal_rec = doc_ref_cal_rec and list(filter(lambda x: x != False, doc_ref_cal_rec)) or []
        if db_field.name == "calculator_id":
            filter_obj = False
            filters = {'active': True}
            filter_obj = CalculatorMaster.objects.filter(**filters)
            kwargs["queryset"] = filter_obj
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def export_csv(self, request, obj):
        absolute_url_reference = request.build_absolute_uri()
        parsed = urlparse(absolute_url_reference)
        next_url = False
        if parsed.query:
            parsed_dict = parse_qs(parsed.query)
            if parsed_dict.get('next', False):
                next_url = parse_qs(parsed.query)['next'][0]
        print('next_url ===', next_url)
        try:
            if settings.DATA_FILE_DIR and obj.document and obj.calculator_id:
                excelfile = settings.DATA_FILE_DIR + obj.document.url
                excelfile = excelfile.replace("/", "\\")
                if excelfile and os.path.exists(excelfile):
                    excel_to_csv(excelfile, calculator_directory=obj.calculator_id.directory_name)
                    obj.status = 'export_csv'
                    obj.save()
                    self.message_user(request, "Export CSV action was performed successfully", level=messages.INFO)
                    # import_csv_database(calculator_id=obj.calculator_id.id,calculator_directory=obj.calculator_id.directory_name)
                    # prepare_csv_import_journal(calculator_id=obj.calculator_id.id,calculator_directory=obj.calculator_id.directory_name)
            else:
                self.message_user(request, "Something went wrong. Please try back after later",
                                  level=messages.ERROR)
        except Exception as e:
            print('\n Exception args ... ', e.args)
            self.message_user(request, "Something went wrong. Please try back after later",
                              level=messages.ERROR)
        if next_url:
            return HttpResponseRedirect(next_url)

    def import_journal(self, request, obj):
        absolute_url_reference = request.build_absolute_uri()
        parsed = urlparse(absolute_url_reference)
        next_url = False
        if parsed.query:
            parsed_dict = parse_qs(parsed.query)
            if parsed_dict.get('next', False):
                next_url = parse_qs(parsed.query)['next'][0]
        print('next_url ===', next_url)
        try:
            if obj.calculator_id:
                import_csv_database(calculator_id=obj.calculator_id.id,
                                    calculator_directory=obj.calculator_id.directory_name)
                prepare_csv_import_journal(calculator_id=obj.calculator_id.id,
                                           calculator_directory=obj.calculator_id.directory_name)
                create_sample_file(calculator_id=obj.calculator_id.id,
                                   calculator_directory=obj.calculator_id.directory_name)
                obj.status = 'import_journal'
                obj.save()
                self.message_user(request, "Import Journal action was performed successfully", level=messages.INFO)
        except Exception as e:
            print('\n Exception args ... ', e.args)
            self.message_user(request, "Something went wrong. Please try back after later",
                              level=messages.ERROR)
        if next_url:
            return HttpResponseRedirect(next_url)

    change_actions = (
        "export_csv",
        "import_journal",
    )

    def get_queryset(self, request):
        self.reference_path = request.path
        return super().get_queryset(request)

    def button_actions(self, obj):
        final_html = '<p> NA </p>'
        if not obj.is_auto:
            export_csv_html_ref = ''
            import_journal_html_ref = ''
            if obj.status == 'draft':
                export_csv_href_link = '{}{}{}{}'.format(self.reference_path, obj.id, '/actions/export_csv/?next=',
                                                         self.reference_path)
                export_csv_html_ref = '<a href="{}" title="" class="grp-button">{}</a>&nbsp;'.format(
                    export_csv_href_link, 'Export CSV')
            if obj.status == 'export_csv':
                import_journal_href_link = '{}{}{}{}'.format(self.reference_path, obj.id,
                                                             '/actions/import_journal/?next=', self.reference_path)
                import_journal_html_ref = '<a href="{}" title="" class="grp-button">{}</a>&nbsp;'.format(
                    import_journal_href_link, 'Import Journal')
            if final_html:
                final_html = '{}{}'.format(export_csv_html_ref, import_journal_html_ref)
                if not final_html:
                    final_html = '<p> No pending actions </p>'
        return format_html(final_html)

    button_actions.short_description = 'Button Actions'
    button_actions.allow_tags = True

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

    readonly_fields = ['created_at']
    fields = (
        'created_at', 'created_by', 'action', 'filter_perc', 'society_approval_rate_perc', 'avg_price_change_perc',
        'status', 'remarks', 'description')

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RateAnalysisAdmin(DjangoObjectActions, admin.ModelAdmin):
    fieldsets = (
        ('Basic Info', {'fields': ('rate_analysis_no', 'scenario_id', 'document_id', 'status'), 'classes': ['wide']}),
        ('Metrics Info', {'fields': ('filter_perc', 'society_approval_rate_perc', 'avg_price_change_perc',),
                          'classes': ['form-row-6columns']}),
        ('', {'fields': ('description', 'remarks',), 'classes': ['form-row-6columns']}),
        ('Log Info',
         {'fields': ('created_at', 'created_by', 'modified_at', 'modified_by'), 'classes': ['form-row-6columns']}),
    )

    change_actions = ("edit_price",)

    inlines = (RateAnalysisDetailsAdminInline, RateAnalysisHistoryAdminInline,)
    list_display = (
        "rate_analysis_no", "scenario_id", "filter_perc", "society_approval_rate_perc", "avg_price_change_perc",
        "status",
        "remarks")
    search_fields = ['rate_analysis_no', 'scenario_id__name', 'status']
    list_filter = ('rate_analysis_no', 'scenario_id', 'status')

    change_form_template = "calc/admin/admin_rate_analysis_change_form.html"

    def edit_price(self, request, obj):
        if obj.status == 'pending':
            return_url = '/financial-analysis/rate_analysis_id={}'.format(str(obj.id))
            return redirect(return_url)
        self.message_user(request, "Invalid Action! Edit price can be performed on pending status",
                          level=messages.ERROR)

    edit_price.attrs = {'target': '_blank'}

    def change_view(self, request, object_id, extra_context=None):
        ''' customize add/edit form '''
        extra_context = extra_context or {}
        # extra_context['objectactions'] = [{"name": "edit_price","label": "Edit Price"}]
        if object_id:
            rate_analysis_obj = RateAnalysis.objects.get(pk=object_id)
            if rate_analysis_obj.status == 'pending':
                extra_context['show_approve'] = True
                extra_context['show_reject'] = True
                extra_context['show_cancel'] = True
                extra_context['show_edit_price'] = True
                extra_context['show_delete'] = True
                extra_context['show_delete_link'] = True
                # extra_context['show_save'] = True
            if rate_analysis_obj.status == 'cancel':
                extra_context['show_reopen'] = True
            if rate_analysis_obj.status in ('approve', 'reject'):
                extra_context['show_reopen'] = True
        return super(RateAnalysisAdmin, self).change_view(request, object_id, extra_context=extra_context)

    def response_change(self, request, obj):
        rate_analysis_rec = obj and RateAnalysis.objects.filter(pk=obj.id) or False
        update_data = {'modified_by': request.user}
        if "_approve" in request.POST:
            print('call approve from response_change ...')
            self.approve(request, obj)
            # update_data.update(status='approve')
            # if rate_analysis_rec and update_data:
            #     rate_analysis_rec.update(**update_data)
            return HttpResponseRedirect(".")
        if "_reject" in request.POST:
            print('call reject from response_change ...')
            self.reject(request, obj)
            # update_data.update(status='reject')
            # if rate_analysis_rec and update_data:
            #     rate_analysis_rec.update(**update_data)
            return HttpResponseRedirect(".")
        if "_cancel" in request.POST:
            print('call cancel from response_change ...')
            self.cancel(request, obj)
            # update_data.update(status='cancel')
            # if rate_analysis_rec and update_data:
            #     rate_analysis_rec.update(**update_data)
            return HttpResponseRedirect(".")
        if "_reopen" in request.POST:
            print('call reopen from response_change ...')
            self.reopen(request, obj)
            # update_data.update(status='pending')
            # if rate_analysis_rec and update_data:
            #     rate_analysis_rec.update(**update_data)
            return HttpResponseRedirect(".")
        if "_edit_price" in request.POST:
            print('call edit price from response_change ...')
            return self.edit_price(request, obj)
            # return HttpResponseRedirect(".")
            pass
        return super().response_change(request, obj)

    def has_add_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        # make all fields readonly
        readonly_fields = self.readonly_fields
        exclude_fileds = ['description', 'remarks']
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
        instance = form.save(commit=False)
        if not hasattr(instance, 'created_by'):
            instance.created_by = request.user
        instance.modified_by = request.user
        instance.save()
        return instance

    def approve(self, request, obj):
        print('approve .....')
        obj.modified_by = request.user
        obj.status = 'approve'
        obj.save()

    def reject(self, request, obj):
        print('reject .....')
        obj.modified_by = request.user
        obj.status = 'reject'
        obj.save()

    def cancel(self, request, obj):
        print('cancel .....')
        obj.modified_by = request.user
        obj.status = 'cancel'
        obj.save()

    def reopen(self, request, obj):
        print('reopen .....')
        obj.modified_by = request.user
        obj.status = 'pending'
        obj.save()


admin.site.register(RateAnalysis, RateAnalysisAdmin)
