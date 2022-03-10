from django.shortcuts import render,redirect
from django.http import HttpResponse
import json
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.models import User
import pandas as pd
import os, sys, traceback
import random
from datetime import timedelta, date

from django_plotly_dash.access import login_required

import calc as c
from .calc import *
from .models import *
import logging

logger = logging.getLogger(__file__)

def index(request):
    if (request.path == '/'):
        return redirect('login')
    return page_index(request)

def logout_view(request):
    logout(request)
    return redirect('login')

def calculator_view(request):
    if (request.path == '/'):
        return redirect('login')
    return page_index(request)

def get_calculator_id(request):
    calculator_id = 0
    if request.user.is_authenticated:
        profile_obj = Profile.objects.filter(user=request.user.id)
        if profile_obj:
            profile_obj = profile_obj.values('profileid', 'calculator_id')[0]
            ref_calculator_id = profile_obj.get('calculator_id',False) and profile_obj.get('calculator_id',False) or calculator_id
            calculator_obj = CalculatorMaster.objects.filter(pk=ref_calculator_id,active=True,is_published=True)
            calculator_obj = calculator_obj and list(calculator_obj) or []
            calculator_id = calculator_obj and ref_calculator_id or calculator_id
    return calculator_id

def page_index(request):
    if request.user.is_authenticated:
        calculator_id = get_calculator_id(request)
        all_calculator_data = []
        if request.user.is_superuser:
            all_calculator_data = CalculatorMaster.objects.filter(active=True,is_published=True).values('id','name').distinct('name')
        return render(request,'calc/calculator.html',{"calculator_id": calculator_id,
                                                      "all_calculator_data": all_calculator_data})
    else:
        return redirect('login')

# JS-AJAX Call
def get_calculator_data(request):
    calculator_id = request.GET.get('calculator_id', False)
    calculator_rec = CalculatorMaster.objects.filter(pk=calculator_id,active=True,is_published=True).values('name', 'primary_currency_id',
                                                                              'currency_ids', 'directory_name')
    calculator_rec = calculator_rec and list(calculator_rec) or []
    if calculator_rec:
        currency_ids = calculator_rec and list(map(lambda x: x['currency_ids'], calculator_rec)) or []
        calculator_rec = calculator_rec and calculator_rec[0] or {}
        primary_currency_id = calculator_rec and calculator_rec.get('primary_currency_id',False) or False
        primary_currency_obj = primary_currency_id and CurrencyMaster.objects.get(pk=primary_currency_id) or {}
        primary_currency_data = primary_currency_obj and {'id': primary_currency_obj.pk, 'code': primary_currency_obj.code , 'name': primary_currency_obj.name} or {}
        journal_code_data = get_journal_details(calculator_directory = calculator_rec.get('directory_name',False),calculator_id = calculator_id)
        output_data = calculator('#', is_inflation=0, is_bypass=1,
                                 calculator_directory=calculator_rec.get('directory_name',False))
        currency_rec = currency_ids and CurrencyMaster.objects.filter(pk__in=currency_ids).values() or []
        currency_rate_rec = currency_ids and CurrencyRateMaster.objects.filter(from_currency__in=[primary_currency_obj.pk], to_currency__in=currency_ids).values() or []
        currency_rate_rec = currency_rate_rec and list(currency_rate_rec) or []
        for rate in currency_rate_rec:
            curr_rec = CurrencyMaster.objects.get(pk=rate['to_currency_id'])
            rate['to_currency_code'] = rate.get('to_currency_id',False) and curr_rec.code or False
        currency_rec = currency_rec and list(currency_rec) or []
        return render(request, 'calc/calculator_view.html', {"form": [output_data],
                                                        "code": journal_code_data,
                                                        "primary_currency_data" : primary_currency_data,
                                                        "currency_data" : currency_rec,
                                                        "currency_rate_data" : currency_rate_rec,
                                                        "calculator_id": calculator_id})
    else:
        return render(request, 'calc/calculator_view.html', {"form": [],
                                                        "code": [],
                                                        "primary_currency_data" : [],
                                                        "currency_data" : [],
                                                        "currency_rate_data" : [],
                                                        "calculator_id": 0})

# JS-AJAX Call
def load_data(request, key):
    output_data = []
    journal_code = request.GET.get('journal_code', False)
    is_adj_inflation = request.GET.get('is_adj_inflation', False)
    calculator_id = request.GET.get('calculator_id', False)
    # profile_obj = Profile.objects.get(user=request.user.id)
    calculator_obj = CalculatorMaster.objects.get(pk=calculator_id,active=True,is_published=True)
    output_data = calculator(journal_code=[journal_code], is_inflation=is_adj_inflation, is_bypass=1, action_type = "ajax-call-read",
                             calculator_directory=calculator_obj and calculator_obj.directory_name or False)
    return HttpResponse(json.dumps(output_data), content_type='application/json')

def analysis_view(request):
    if (request.path == '/'):
        return redirect('login')
    profile_rec = Profile.objects.filter(user=request.user.id)
    if profile_rec:
        profile_obj = Profile.objects.get(user=request.user.id)
        if profile_obj.calculator_id:
            if profile_obj.calculator_id.active == True and profile_obj.calculator_id.is_published == True:
                output_data = analysis(calculator_directory = profile_obj.calculator_id and profile_obj.calculator_id.directory_name or False)
                context = {
                    'ownership': output_data['ownership']
                }
                return HttpResponse(render(request, 'calc/analysis.html',context))
            else:
                return redirect('login')
    else:
        return redirect('login')

def get_profile(request):
    if request.user.is_authenticated:
        current_user = request.user
        if current_user:
            queryset  = User.objects.filter(id = current_user.id)
            usr_obj = queryset[0]
            context ={
                'usr_obj':usr_obj
            }
            return HttpResponse(render(request,'profile.html',context))
    else:
        return redirect("login")

def financial_analysis_view(request):
    calculator_id = 0
    calc_filters = {'active': True, 'is_published': True}
    if request.user.is_authenticated:
        if not request.user.is_superuser:
            profile_obj = Profile.objects.get(user=request.user.id)
            calculator_rec = profile_obj and profile_obj.calculator_id or False
            calculator_id = calculator_rec and calculator_rec.id or 0
            if calculator_id:
                calc_filters['pk'] = calculator_id
        calc_filter_obj = CalculatorMaster.objects.filter(**calc_filters).values('pk').distinct()
        calc_filter_obj = calc_filter_obj and list(calc_filter_obj) or []
        calc_filter_obj = len(calc_filter_obj)>0 and calc_filter_obj[0] or calc_filter_obj
        calculator_id = calc_filter_obj and calc_filter_obj.get('pk',0) or calculator_id
        context = {'dash_input': {
                                    'user_id': {'value': request.user.id},
                                    'calculator_id': {'value': calculator_id},
                                    # 'fig_dropdown': {'value': calculator_id},
                                },
                  }
        return render(request, 'calc/financial_analysis.html', context)
    return redirect('login')


def financial_analysis_report(request):
    if request.user.is_authenticated:
        calculator_id = get_calculator_id(request)
        scenario_data = RateAnalysis.objects.filter(created_by = request.user.id)

        context = {
                    'user_id': {'value': request.user.id},
                    'calculator_id': {'value': calculator_id},
                    'scenario_data': {'value': scenario_data}
                }
        print(context)
        return render(request, 'calc/financial_analysis_report.html', context)
    return redirect('login')
