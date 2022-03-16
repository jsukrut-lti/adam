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
        return render(request, 'home.html')
        # calculator_id = get_calculator_id(request)
        # all_calculator_data = []
        # if request.user.is_superuser:
        #     all_calculator_data = CalculatorMaster.objects.filter(active=True,is_published=True).values('id','name').distinct('name')
        # return render(request,'calc/calculator.html',{"calculator_id": calculator_id,
        #                                               "all_calculator_data": all_calculator_data})
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

# def financial_analysis_view(request):
#     print ('\n financial_analysis_view')
#     from django_plotly_dash import DjangoDash
#     # from .analysis import layout
#     data = {'symbol': 'Ƀ 0.0',
#      'btc_percentage': 10.00,
#      'bitcoin_balance': 3000,
#      'usd_percentage': 23.25,
#      'usd_balance': 4000,
#      'user_usd_balance': '5000',
#      'user_btc_balance': 2400,
#      'user_btc_value': '2350',
#      'portfolio_balance': '1900',
#      'change': 12,
#      # 'transaction': transaction,
#      'message': '* Reset will delete the transactions history...'}
#     return render(request, 'calc/financial_analysis.html', data)

# def session_state_view(request, template_name, **kwargs):
#
#     session = request.session
#
#     demo_count = session.get('django_plotly_dash', {})
#
#     ind_use = demo_count.get('ind_use', 0)
#     ind_use += 1
#     demo_count['ind_use'] = ind_use
#     session['django_plotly_dash'] = demo_count
#
#     # Use some of the information during template rendering
#     context = {'ind_use' : ind_use}
#
#     return render(request, template_name=template_name, context=context)

# import pandas as pd
# from django.conf import settings
# from calc.models import *
# import datetime
# import itertools
# from django.shortcuts import render,redirect
# from dash import dcc, html, callback_context, dash_table as dt
# from dash.dash_table import DataTable, FormatTemplate
# from dash.dash_table.Format import Format, Group
# import plotly.express as px
# from dash.dependencies import Input, Output, State, MATCH, ALL
# from dash.exceptions import PreventUpdate
# import plotly.graph_objs as go
# from django_plotly_dash import DjangoDash
# import logging
# logger = logging.getLogger(__file__)
#
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',{'href':'http://127.0.0.1:8000/static/calc/css/style.css', 'rel': 'stylesheet'}]
# app = DjangoDash('AnalysisApp', external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
#
# sales = pd.read_csv('C:\\Users\\Lenovo\\Documents\\GitHub\\wileydash\\scripts\\train.csv')
# percentage = FormatTemplate.percentage(2)
#
# ### Test Data
# column_names = ["APC change %",
#                 "N-Number of journals", "N-Revenue change $",
#                 "J-Number of journals", "J-Revenue change $",
#                 "O-Number of journals", "O-Revenue change $",
#                 "Total Number of journals",
#                 "Total Number of journals1",
#                 "Total Number of journals2",
#                 "Total Number of journals3",
#                 "Total Number of journals4",
#                 "Total Number of journals5",
#                 "Total Revenue change $"]
# df = pd.DataFrame(columns = column_names)
# df = df.append({
#                 'APC change %' : '1-2%',
#                 'N-Number of journals' : 78,
#                 'N-Revenue change $' : 109531,
#                 'J-Number of journals' : 50,
#                 'J-Revenue change $' : 69475,
#                 'O-Number of journals' : 225,
#                 'O-Revenue change $' : 344570,
#                 'Total Number of journals' : 353,
#                 'Total Revenue change $' : 523576,
#                 }, ignore_index = True)
# df = df.append({
#                 'APC change %' : '3-5%',
#                 'N-Number of journals' : 5,
#                 'N-Revenue change $' : 12450,
#                 'J-Number of journals' : 9,
#                 'J-Revenue change $' : 97520,
#                 'O-Number of journals' : 95,
#                 'O-Revenue change $' : 257232,
#                 'Total Number of journals' : 109,
#                 'Total Revenue change $' : 367202,
#                 }, ignore_index = True)
# df = df.append({
#                 'APC change %' : '6-10%',
#                 'N-Number of journals' : 4,
#                 'N-Revenue change $' : 14576,
#                 'J-Number of journals' : 7,
#                 'J-Revenue change $' : 56780,
#                 'O-Number of journals' : 41,
#                 'O-Revenue change $' : 307496,
#                 'Total Number of journals' : 52,
#                 'Total Revenue change $' : 378753,
#                 }, ignore_index = True)
# print(df)
#
# colors = {
#     'background': '#ffffff',
#     'text': '#212529'
# }
#
# app.layout = html.Div([
#     html.Div([
#         html.Div([
#             html.P('Select Scenario', className='fix_label',
#                    style={'color': colors['text']}),
#             dcc.Dropdown(id='fig_dropdown',
#                          options=[{'label': i, 'value': i}
#                                   for i in ['BAU - min 2%, max 20%', 'Summary - Max % increase', 'Summary - Volume threshold', 'Impact Factor threshold']],
#                          value='Summary - Max % increase',
#                          style={'textAlign': 'left', 'color': 'black',
#                                 'height': '36px', 'width': '290px'},
#                          className='dcc_compon'),
#         ], className='one-third column', id='title13', style={'margin-left':'0','width': '100%'}),
#
#         html.Div([
#             html.P('Society Approval Rate (%)', className='fix_label',
#                    style={'color': colors['text']}),
#             dcc.Input(id='approval_rate', type='number', value=20.00,
#                       style={'height': '36px', 'width': '290px'},
#                       ),
#         ], className='one-third column', id='title4', style={'margin-left':'0'}),
#
#         html.Div([
#             html.P('Average Price Increase', className='fix_label',
#                    style={'color': colors['text']}),
#             dcc.Input(id='avg_price_increase', type='text', value="0.00%",
#                       style={'height': '36px', 'width': '290px'},
#                       ),
#         ], className='one-third column', id='title6', style={'margin-left':'0'}),
#
#         html.Div([
#             html.P('Combined average price increase (Gold + Hybrid)',
#                    className='fix_label', style={'color': colors['text']},
#                    ),
#             dcc.Input(id='comb_avg_price_increase', type='text', value="0.00%",
#                       style={'height': '36px', 'width': '290px'},
#                       # format=Format(symbol_suffix=percentage).group(True).precision(0),
#                       ),
#         ], className='one-third column', id='title7', style={'margin-left':'0'}),
#
#     ], style={'display': 'flex', 'flex-wrap':'wrap', 'justify-content':'start', 'align-items':'center', 'row-gap':'30px', 'gap': '30px', 'margin-bottom':'30px'}),
#
#     html.Div([
#         html.Div([
#             dt.DataTable(id='my_datatable2',
#                          columns=[
#                              {"name": ["", "APC change %"], "id": "APC change %"},
#                              {"name": ["N-Society Owned", "Number of journals"], "id": "N-Number of journals"},
#                              {"name": ["N-Society Owned", "Revenue change $"], "id": "N-Revenue change $"},
#                              {"name": ["J-Joint Owned", "Number of journals"], "id": "J-Number of journals"},
#                              {"name": ["J-Joint Owned", "Revenue change $"], "id": "J-Revenue change $"},
#                              {"name": ["O-Proprietary Owned", "Number of journals"], "id": "O-Number of journals"},
#                              {"name": ["O-Proprietary Owned", "Revenue change $"], "id": "O-Revenue change $"},
#                              {"name": ["", "Total Number of journals"], "id": "Total Number of journals"},
#                              {"name": ["", "Total Number of journals1"], "id": "Total Number of journals1"},
#                              {"name": ["", "Total Number of journals2"], "id": "Total Number of journals2"},
#                              {"name": ["", "Total Number of journals3"], "id": "Total Number of journals3"},
#                              {"name": ["", "Total Number of journals4"], "id": "Total Number of journals4"},
#                              {"name": ["", "Total Number of journals5"], "id": "Total Number of journals5"},
#                              {"name": ["", "Total Revenue change $"], "id": "Total Revenue change $"},
#                          ],
#
#                          virtualization=True,
#                          style_cell={'textAlign': 'center',
#                                      'min-width': '100px',
#                                      'backgroundColor': '#1f2c56',
#                                      'color': '#FEFEFE',
#                                      'border-bottom': '0.01rem solid #19AAE1',
#                                      'font-size': '15px',
#                                      'height': '40px'},
#                          style_header={'backgroundColor': '#1f2c56',
#                                        'fontWeight': 'bold',
#                                        'font': 'Lato, sans-serif',
#                                        'color': 'orange',
#                                        'border': '#1f2c56',
#                                        'font-size': '18px'},
#                          style_as_list_view=True,
#                          style_data={'styleOverflow': 'hidden',
#                                      'color': 'white', 'font-size': '14px',
#                                      'font-weight': '520',
#                                      'font-family': 'sans-serif'},
#                          fixed_rows={'headers': True},
#                          sort_action='native',
#                          page_size=6,
#                          style_header_conditional=[
#                              {'if': {'column_id': 'Customer ID', 'header_index': 0},
#                               'text-align': '-webkit-center'},
#                              {'if': {'column_id': 'Customer Name',
#                                      'header_index': 0}, 'text-align': '-webkit-center'},
#                              {'font-size': '16px',
#                               'font-weight': '580',
#                               'font-family': 'sans-serif'}
#                          ],
#                          merge_duplicate_headers=True,
#                          sort_mode='multi')
#
#         ], className='create_container2'),
#
#     ], className='row flex-display')
#
# ], id='mainContainer', style={'display': 'flex', 'flexDirection': 'column', 'padding':'15px'})
#
#
# @app.callback(Output('my_datatable2', 'data'),
#               Output('comb_avg_price_increase', 'value'),
#               [Input('approval_rate', 'value'), Input('fig_dropdown', 'value')])
# def update_datatable(approval_rate, fig_dropdown):
#     print('fig_dropdown=====',fig_dropdown)
#     data_table = df
#     return [data_table.to_dict('records'),'17.00%']

