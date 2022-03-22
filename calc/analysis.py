import sys, os
import pandas as pd
import uuid
from django.db import transaction
import re
from django.conf import settings
from .calc import *
from calc.models import *
import io
import base64
import itertools
from django.shortcuts import render, redirect
import dash_bootstrap_components as dbc
from dash import dcc, html, callback_context, dash_table as dt
from dash.dash_table import DataTable, FormatTemplate
from dash.dash_table.Format import Format, Group, Scheme, Symbol, Sign
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from django_plotly_dash import DjangoDash
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np
import visdcc
import logging
import math

logger = logging.getLogger(__file__)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',
                        {'href': 'http://127.0.0.1:8000/static/calc/css/style.css', 'rel': 'stylesheet'},
                        # dbc.themes.BOOTSTRAP
                        ]
app = DjangoDash('AnalysisApp', external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

colors = {
    'background': '#ffffff',
    'text': '#212529'
}

alert = dbc.Alert("Testing ... ", color="danger", dismissable=True)

app.layout = html.Div([
    visdcc.Run_js(id='javascript'),
    html.Div([
        html.Div([
            dcc.Input(id='user_id', persistence=False, readOnly=True, value=0)], style={'display': 'none'}),
        html.Div([
            dcc.Input(id='calculator_id', persistence=False, readOnly=True, value=0)], style={'display': 'none'}),
        html.Div([
            dcc.Input(id='rate_analysis_id', persistence=False, readOnly=True, value=0)], style={'display': 'none'}),
        html.Div([
            dcc.Input(id='document_id', persistence=False, readOnly=True, value=0)], style={'display': 'none'}),
        # html.A('Download *SELECTED* Data',id='download-selection',href="",target="_blank"),
        html.Div([
            html.Div([
                html.P('Select Scenario', className='fix_label',
                       style={'color': colors['text']}),
                dcc.Dropdown(id='scenario_id',
                             options=[],
                             value='',
                             style={'textAlign': 'left', 'color': 'black'},
                             className='dcc_compon'),
                html.Div(id="valid_scenario_id", style={"color": "red", "fontSize": "12px"})], className='four columns',
                id='title13'),
            html.Div([
                dcc.Upload(
                    id='datatable-upload',
                    children=html.Div([
                        html.Img(
                            src='http://127.0.0.1:8000/static/calc/images/upload.png',
                        ),
                        html.Img(
                            src='http://127.0.0.1:8000/static/calc/images/download1.png',
                        )
                    ], className='uploadImg'),
                ),
            ], className='ml-0', id='upload_file'),
        ], className='ddContainer'),
        dcc.ConfirmDialog(
            id='confirm-danger',
            message='Are you sure you want to continue?',
        ),
        html.Div(id="the_alert", children=[], style={'display': 'none'}),
        html.Div([
            html.P('Filter Percentage', className='fix_label',
                   style={'color': colors['text']}),
            dcc.Input(id='filter_perc', type='number', value=20.00, required=True,
                      ),
        ], className='ml-0', id='title0'),
        html.Div([
            html.P('Society Approval Rate (%)', className='fix_label',
                   style={'color': colors['text']}),
            dcc.Input(id='society_approval_rate_perc', type='number', value=50.00, required=True,
                      ),
        ], className='ml-0', id='title4'),
        html.Div([
            html.P('Average Price Increase (%)', className='fix_label',
                   style={'color': colors['text']}),
            dcc.Input(id='avg_price_change_perc', type='number', value=0.00, readOnly=True,
                      ),
        ], className='ml-0', id='title6'),
        html.Div([
            html.P('Combined average price increase (Gold + Hybrid) %',
                   className='fix_label', style={'color': colors['text']},
                   ),
            dcc.Input(id='comb_avg_price_increase', type='number', value=0.00, readOnly=True,
                      ),
        ], className='ml-0', id='title7'),
        html.Div([
            html.P('Notes', className='fix_label',
                   style={'color': colors['text']}),
            dcc.Input(id='description', type='text', value='',
                      ),
        ], className='ml-0', id='title00'),
        html.Div([
            html.P('Approve/Reject Remarks', className='fix_label',
                   style={'color': colors['text'], 'display': 'none'}),
            dcc.Input(id='remarks', type='text', value='', style={'display': 'none'}
                      ),
        ], className='ml-0', id='title000'),
    ], className='topSection'),
    html.Div([
        html.Button(id='apply-button-state', className='btnApply', children="Apply Changes"),
        html.Button(id='export-button-state', className='btnExport', children="Export"),
        html.Button(id='submit-button-state', className='btnSubmit', children="Submit")
    ], className='btnContainer'),
    html.Div([
        html.Div([
            dt.DataTable(id='datatable',
                         columns=[
                             {"name": ["", "APC change %"], "id": "APC change %"},
                             {"name": ["N-Society Owned", "Number of journals"],
                              "id": "N-Number of Journals"},
                             {"name": ["N-Society Owned", "Revenue change $"],
                              "id": "N-Revenue change",
                              "type": "numeric",
                              'format': Format(
                                  precision=2,
                                  scheme=Scheme.fixed,
                                  symbol=Symbol.yes,
                                  symbol_prefix="{} ".format(Symbol.yes),
                                  group=','
                              )},
                             {"name": ["J-Joint Owned", "Number of journals"], "id": "J-Number of Journals"},
                             {"name": ["J-Joint Owned", "Revenue change $"],
                              "id": "J-Revenue change",
                              "type": "numeric",
                              'format': Format(
                                  precision=2,
                                  scheme=Scheme.fixed,
                                  symbol=Symbol.yes,
                                  symbol_prefix="{} ".format(Symbol.yes),
                                  group=','
                              )},
                             {"name": ["O-Proprietary Owned", "Number of journals"], "id": "O-Number of Journals"},
                             {"name": ["O-Proprietary Owned", "Revenue change $"],
                              "id": "O-Revenue change",
                              "type": "numeric",
                              'format': Format(
                                  precision=2,
                                  scheme=Scheme.fixed,
                                  symbol=Symbol.yes,
                                  symbol_prefix="{} ".format(Symbol.yes),
                                  group=','
                              )},
                             {"name": ["", "Total Number of Journals $"], "id": "Total-Number of Journals"},
                             {"name": ["", "Total Revenue change $"],
                              "id": "Total-Revenue change",
                              "type": "numeric",
                              'format': Format(
                                  precision=2,
                                  scheme=Scheme.fixed,
                                  symbol=Symbol.yes,
                                  symbol_prefix="{} ".format(Symbol.yes),
                                  group=','
                              )},
                         ],
                         # virtualization=True,
                         export_format="xlsx",
                         export_headers="display",
                         style_cell={},
                         style_header={},
                         style_as_list_view=True,
                         style_data={'styleOverflow': 'hidden'},
                         sort_action='native',
                         page_size=20,
                         merge_duplicate_headers=True,
                         )
        ], className='create_container2'),
    ], className='tableContainer'),
    html.Br(),
    html.Div([
        html.P('Rate Analysis Graph', style={'display': 'block', "fontSize": "16px", 'color': 'black'}),
        dcc.Graph(id='bar-scratter-graph'),
    ], style={'display': 'block'})
], id='mainContainer'
)


def save_file(name, content, filepath, output_filepath):
    print('save file .....')
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(filepath, name), "wb") as fp:
        fp.write(base64.decodebytes(data))
    output = '{}\{}'.format(output_filepath, name)
    return output


@transaction.atomic()
def create_or_update_record(save=True, **kwargs):
    print('create or update ....')
    input_data = kwargs.get('input_data', False)
    inputline_data = input_data.get('datatable', [])
    user_obj = User.objects.get(pk=int(input_data.get('user_id')))
    calculator_obj = CalculatorMaster.objects.get(pk=int(input_data.get('calculator_id')))
    scenario_obj = ScenarioMaster.objects.get(pk=int(input_data.get('scenario_id')))
    if input_data.get('action') == 'create':
        document_data = {'calculator_id': calculator_obj,
                         'scenario_id': scenario_obj,
                         'name': 'Auto entry from Rate Analysis holds user input document',
                         'document': input_data.get('filename', False)}
        document_rec = Document.objects.create(**document_data)
    parent_data = {'calculator_id': calculator_obj,
                   'scenario_id': scenario_obj,
                   'filter_perc': input_data.get('filter_perc'),
                   'society_approval_rate_perc': input_data.get('society_approval_rate_perc', 0.00),
                   'avg_price_change_perc': input_data.get('avg_price_change_perc', 0.00),
                   'status': 'pending',
                   'remarks': input_data.get('remarks', ''),
                   'description': input_data.get('description', ''),
                   }
    if input_data.get('action') == 'create':
        parent_data.update({
            'document_id': document_rec,
            'user_id': user_obj,
            'created_by': user_obj
        })
        rate_analysis_rec = RateAnalysis.objects.create(**parent_data)
    if input_data.get('action') == 'edit':
        rate_analysis_rec = RateAnalysis.objects.filter(pk=int(input_data.get('rate_analysis_id'))). \
            values('filter_perc', 'society_approval_rate_perc', 'avg_price_change_perc',
                   'status', 'remarks', 'description')
        rate_analysis_rec = rate_analysis_rec and list(rate_analysis_rec) or []
        rate_analysis_rec_data = rate_analysis_rec and rate_analysis_rec[0] or {}
        history_data = {}
        if rate_analysis_rec_data:
            for key, value in rate_analysis_rec_data.items():
                if parent_data.get(key) == value:
                    parent_data.pop(key, None)
                else:
                    history_data[key] = value
        parent_data.update({
            'modified_by': user_obj
        })
        rate_analysis_update_rec = RateAnalysis.objects.filter(pk=int(input_data.get('rate_analysis_id'))).update(
            **parent_data)
        rate_analysis_rec = RateAnalysis.objects.get(pk=int(input_data.get('rate_analysis_id')))
        if history_data:
            history_data.update({'rate_analysis_id': rate_analysis_rec, 'action': 'modify', 'created_by': user_obj})
            history_data and RateAnalysisHistory.objects.create(**history_data) or False
    parent_sp = transaction.savepoint()
    inline_data = [{'apc_change_perc': 'APC change %',
                    'ownership_structure': 'N-Society Owned',
                    'journal_count': 'N-Number of Journals',
                    'revenue_change': 'N-Revenue change'},
                   {'apc_change_perc': 'APC change %',
                    'ownership_structure': 'J-Joint Owner',
                    'journal_count': 'J-Number of Journals',
                    'revenue_change': 'J-Revenue change'},
                   {'apc_change_perc': 'APC change %',
                    'ownership_structure': 'O-Proprietary Owned',
                    'journal_count': 'O-Number of Journals',
                    'revenue_change': 'O-Revenue change'}]
    if input_data.get('action') == 'edit':
        RateAnalysisDetails.objects.filter(rate_analysis_id=int(input_data.get('rate_analysis_id'))).delete()
    if inputline_data:
        for var in inputline_data:
            filtered_var = {k: v for k, v in var.items() if v is not None}
            if 'Total' not in filtered_var.get('APC change %', False):
                for line in inline_data:
                    is_present_list = []
                    outline_data = {}
                    for key, value in line.items():
                        if key in ['journal_count', 'revenue_change']:
                            if filtered_var.get(value, False):
                                outline_data[key] = filtered_var.get(value, False)
                                is_present_list.append(1)
                    if is_present_list and max(is_present_list) == 1 or False:
                        outline_data['ownership_structure'] = line.get('ownership_structure')
                        apc_perc_val = line.get('apc_change_perc', False) and filtered_var.get(
                            line.get('apc_change_perc', False), False) or False
                        if apc_perc_val:
                            outline_data['apc_change_perc'] = apc_perc_val
                    if outline_data:
                        outline_data['rate_analysis_id'] = rate_analysis_rec
                        rate_analysis_detail_rec = RateAnalysisDetails.objects.create(**outline_data)
    if save:
        transaction.savepoint_commit(parent_sp)
    else:
        transaction.savepoint_rollback(parent_sp)
    print('\n rate_analysis_rec ====', rate_analysis_rec.rate_analysis_no)
    # stop
    return rate_analysis_rec.rate_analysis_no


def parse_contents(**kwargs):
    print('parse content ....')
    file_data = kwargs.get('file_data', False)
    contents = file_data and file_data.get('contents', False)
    filename = file_data and file_data.get('filename', False)
    action = file_data and file_data.get('action', False)
    document_dynamic_filepath = file_data and file_data.get('document_dynamic_filepath', False)
    if contents and filename:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        if not action:
            if 'csv' in filename:
                # Assume that the user uploaded a CSV file
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                return df
            elif 'xls' in filename:
                # Assume that the user uploaded an excel file
                df = pd.read_excel(io.BytesIO(decoded))
                return df
        else:
            new_filepath = os.path.join(settings.MEDIA_ROOT, document_dynamic_filepath, filename)
            if not os.path.exists(os.path.join(settings.MEDIA_ROOT, document_dynamic_filepath)):
                os.makedirs(os.path.join(settings.MEDIA_ROOT, document_dynamic_filepath))
            if os.path.exists(new_filepath):
                fname = os.path.splitext(filename)[0]
                extension = os.path.splitext(filename)[1]
                new_filename = '{}{}{}'.format(fname, str(uuid.uuid4()), extension)
                filename = new_filename
            dynamic_filepath = os.path.join(settings.MEDIA_ROOT, document_dynamic_filepath)
            return save_file(filename, contents, dynamic_filepath, document_dynamic_filepath)


def get_rate_analysis_dataframe(**kwargs):
    print('get_calculator_file ......')
    document_obj = Document.objects.get(pk=int(kwargs.get('document_id')))
    document = document_obj and document_obj.document or False
    document = document and document.path or False
    if document:
        if os.path.exists(document):
            from pathlib import Path
            if Path(document).suffix == '.csv':
                print('\n uploaded file is csv ......')
                return pd.read_csv(document)
    return pd.DataFrame()


def prepare_pivot(**kwargs):
    print('prepare pivot ...')
    dataframe = kwargs.get('dataframe', False)
    society_approval_rate_perc = kwargs.get('society_approval_rate_perc', False)
    filter_perc = kwargs.get('filter_perc', False)
    columns = ['Journal Code', 'Journal', 'Percentage Change', 'Ownership Structure',
               '% category', 'Revenue change']
    try:
        dataframe = pd.DataFrame(dataframe, columns=columns)
        dataframe_filter = dataframe.loc[dataframe['Percentage Change'] <= (filter_perc / 100)]
        if not dataframe_filter.empty:
            dataframe_filter = dataframe.loc[dataframe['Percentage Change'] <= (filter_perc / 100)]
        else:
            dataframe_filter = dataframe

        table = pd.pivot_table(data=dataframe_filter,
                               values=['Journal Code', 'Revenue change', 'Percentage Change'],
                               index=['% category'],
                               columns=['Ownership Structure'],
                               aggfunc={'Journal Code': len,
                                        'Revenue change': np.sum,
                                        'Percentage Change': np.sum},
                               margins=True, margins_name='Total'). \
            reset_index().rename(columns={'Journal Code': 'Number of Journals',
                                          '% category': 'APC change %'})
        table.columns = list(map(lambda x: '-'.join([x[1].split('-')[0], x[0]])
        if x[1].find('-') != -1 else '-'.join([x[1], x[0]])
        if x[1] != '' else ''.join([x[0], x[1]]), table.columns))
        table["Order_By"] = list(map(lambda x: 100
        if x.find('Total') != -1 else float(x.split('-')[0])
        if x.find('-') != -1 else float(re.findall(r'\d+', x)[0]),
                                     table['APC change %']))
        table = table.sort_values(by=['Order_By'], ascending=True)
        table = table.drop(['Order_By'], axis=1)
        table.reset_index(inplace=True)
        table = table.drop(['index'], axis=1)
        table.infer_objects().dtypes
        average_prie_increase = math.ceil((dataframe_filter['Percentage Change'].mean() * 100) * (
                    1 - (society_approval_rate_perc / 100)))

        table = prepare_approval_data(dataframe=table, society_approval_rate_perc=society_approval_rate_perc)
    except Exception as e:
        print('\n Exception args ... ', e.args)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return pd.DataFrame(), 0.00
    return table, average_prie_increase


def prepare_graph(**kwargs):
    print('prepare graph ...')
    dataframe = kwargs.get('dataframe', False)
    scenario_id = kwargs.get('scenario_id', False)
    layout_title = ''
    if scenario_id > 0:
        scenario_rec = ScenarioMaster.objects.filter(id=int(scenario_id))
        scenario_rec = scenario_rec and list(scenario_rec) or []
        scenario_rec = scenario_rec and scenario_rec[0] or False
        layout_title = scenario_rec and u'Graph View - {}'.format(scenario_rec.name) or layout_title

    filter_perc = kwargs.get('filter_perc', False)
    columns = ['Journal Code', 'Journal', 'Percentage Change', 'Ownership Structure',
               '% category', 'Revenue change']
    try:
        dataframe = pd.DataFrame(dataframe, columns=columns)
        dataframe_filter = dataframe.loc[dataframe['Percentage Change'] <= (filter_perc / 100)]
        if not dataframe_filter.empty:
            dataframe_filter = dataframe.loc[dataframe['Percentage Change'] <= (filter_perc / 100)]
        else:
            dataframe_filter = dataframe
        df_plot = dataframe_filter
        pivot_graph = pd.pivot_table(df_plot,
                                     index=['% category'],
                                     columns=["Ownership Structure"],
                                     values=['Journal Code', 'Percentage Change', 'Revenue change'],
                                     aggfunc={'Journal Code': len,
                                              'Revenue change': np.sum,
                                              'Percentage Change': np.sum},
                                     fill_value=0).rename(columns={'% category': 'APC change %'})
        trace1 = go.Bar(x=pivot_graph.index, y=pivot_graph[('Journal Code', 'J-Joint Owned')],
                        name='J-Joint Owned Journal numbers',
                        marker=dict(color='#919799')
                        )
        trace2 = go.Bar(x=pivot_graph.index, y=pivot_graph[('Journal Code', 'N-Society Owned')],
                        name='N-Society Owned Journal numbers',
                        marker=dict(color='#80c178')
                        )
        trace3 = go.Bar(x=pivot_graph.index, y=pivot_graph[('Journal Code', 'O-Proprietary Owned')],
                        name='O-Proprietary Owned Journal numbers',
                        marker=dict(color='#db93ae')
                        )

        trc01 = go.Scatter(x=pivot_graph.index, y=pivot_graph[('Revenue change', 'J-Joint Owned')], yaxis='y2',
                           line=dict(color='#8a11e3'),
                           name='J-Joint Owned Revenue change')
        trc02 = go.Scatter(x=pivot_graph.index, y=pivot_graph[('Revenue change', 'N-Society Owned')], yaxis='y2',
                           line=dict(color='#d2d537'),
                           name='N-Society Owned Revenue change')
        trc03 = go.Scatter(x=pivot_graph.index, y=pivot_graph[('Revenue change', 'O-Proprietary Owned')],
                           yaxis='y2', line=dict(color='red'),
                           name='O-Proprietary Owned Revenue change')
        layout = go.Layout(
            title=layout_title,
            xaxis=dict(
                title='APC %', zeroline=True,
                showline=True
            ),
            yaxis=dict(
                title='Number of Journals', zeroline=True,
                showline=True
            ),
            yaxis2=dict(
                title='Revenue Change',
                zeroline=True,
                showline=True,
                overlaying='y',
                side='right'
            ), legend=dict(y=-0.90, x=0.8))
        fig_layout = {
            'data': [trace1, trace2, trace3, trc01, trc02, trc03],  # trace4
            'layout': layout
        }
        return fig_layout
    except Exception as e:
        print('\n Exception graph args ... ', e.args)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return {}
    return {}


def prepare_approval_data(**kwargs):
    print('prepare approval data ...')
    dataframe = kwargs.get('dataframe', False)
    dataframe.iloc[:,1:] = dataframe.iloc[:,1:].apply(pd.to_numeric).apply(np.ceil)
    approval_rate = kwargs.get('society_approval_rate_perc', False)

    df_zero = {}
    for col in dataframe.columns:
        if col.find('-') != -1 and col.split('-')[0] == "N":
            if col.split('-')[1] == "Number of Journals":
                df_zero_df = dataframe.loc[dataframe['APC change %'] == 'Total', [col]].sum(axis = 0, skipna = True).apply(pd.to_numeric).apply(np.ceil)

            dataframe.loc[1:dataframe.index[-2],[col]] = dataframe[col].apply(lambda x: math.ceil((x * approval_rate) / 100))

    df_zero = df_zero_df.to_dict()

    if '0%' not in dataframe['APC change %'].unique():
        dataframe.loc[-1] = [0] * len(dataframe.columns)
        dataframe.index = dataframe.index + 1
        dataframe.sort_index(inplace=True)
        dataframe['APC change %'][0] = "0%"

    for key, value in df_zero.items():
        dataframe.loc[0:0,key] = dataframe[key].apply(
            lambda x: math.ceil(value - dataframe.loc[1:dataframe.index[-2],[key]].sum()))

    for col in dataframe.columns:
        if col.find('Total') != -1:
            dataframe[col] = dataframe[[dif_col for dif_col in dataframe.columns
                                        if dif_col.find('-') != -1 and dif_col.split('-')[1] == col.split('-')[1]
                                        and dif_col.find('Total') == -1]].sum(axis=1).apply(pd.to_numeric).apply(np.ceil)


    dataframe.loc[dataframe.index[-1],1:] = dataframe.iloc[0:-1,1:].sum(axis=0).apply(pd.to_numeric).apply(np.ceil)

    return dataframe


def get_calculator_directory(**kwargs):
    print('get calc dir...........', kwargs)
    calculator_id = kwargs.get('calculator_id', 0)
    user_id = kwargs.get('user_id', 0)
    calculator_directory = False
    if calculator_id <= 0:
        profile_obj = Profile.objects.get(user=int(user_id))
        calculator_id = profile_obj.calculator_id and profile_obj.calculator_id.id or calculator_id
    if calculator_id > 0:
        calculator_obj = CalculatorMaster.objects.get(pk=int(calculator_id))
        calculator_directory = calculator_obj and calculator_obj.directory_name or calculator_directory
    return calculator_directory


@app.callback(Output('scenario_id', 'options'),
              Output('scenario_id', 'value'),
              [Input('user_id', 'value')])
def update_scenario(user_id):
    print('update_scenario ...')
    scenario_obj1 = ScenarioMaster.objects.values('pk', 'name')
    scenario_list1 = scenario_obj1 and list(scenario_obj1) or []
    if scenario_obj1:
        return [{'label': i.get('name'), 'value': i.get('pk')} for i in scenario_list1], scenario_list1[0].get('pk')
    return [{}], ''


@app.callback(Output('javascript', 'run'),
              Input('submit-button-state', 'n_clicks'),
              Input('scenario_id', 'value'),
              State('rate_analysis_id', 'value'),
              State('user_id', 'value'),
              State('calculator_id', 'value'),
              State('filter_perc', 'value'),
              State('society_approval_rate_perc', 'value'),
              State('avg_price_change_perc', 'value'),
              State('remarks', 'value'),
              State('description', 'value'),
              State('datatable', 'data'),
              State('datatable', 'columns'),
              State('datatable-upload', 'contents'), State('datatable-upload', 'filename')
              )
def update_output(submit_btn, scenario_id, rate_analysis_id, user_id, calculator_id, filter_perc,
                  society_approval_rate_perc, avg_price_change_perc, remarks, description, datatable, datatable_column,
                  contents, filename):
    print('\n update_output ...')
    input_data = {'scenario_id': scenario_id,
                  'calculator_id': calculator_id,
                  'user_id': user_id,
                  'filter_perc': filter_perc,
                  'society_approval_rate_perc': society_approval_rate_perc,
                  'avg_price_change_perc': avg_price_change_perc,
                  'remarks': remarks,
                  'description': description,
                  'datatable': datatable,
                  'filename': filename,
                  'action': 'create'
                  }
    if rate_analysis_id > 0:
        input_data['action'] = 'edit'
        input_data['rate_analysis_id'] = rate_analysis_id
    # update_rate_analysis(input_data = input_data)
    if scenario_id != 0 and society_approval_rate_perc != 0 and avg_price_change_perc != 0 and submit_btn and datatable != [
        [{}], []]:
        print('\n yes')
        if rate_analysis_id > 0:
            reference_number = create_or_update_record(input_data=input_data)
            message_one = 'Your request was successfully submitted for processing. To view the status, use the Reference ID'
            message_two = '{} : {}'.format(message_one, reference_number)
            message_three = 'window.open("{}","_parent");'.format('/financial-analysis-report')
            res = 'alert("{}");'.format(message_two)
            res = '{}{}'.format(res, message_three)
            return res
        else:
            calculator_directory = get_calculator_directory(user_id=input_data.get('user_id', 0),
                                                            calculator_id=input_data.get('calculator_id', 0))
            if calculator_directory:
                document_dynamic_filepath = get_upload_to(calculator_directory, False)
                file_data = {'contents': contents,
                             'filename': filename,
                             'action': True,
                             'document_dynamic_filepath': document_dynamic_filepath
                             }
                document_filepath = parse_contents(file_data=file_data)
                input_data['filename'] = document_filepath
                reference_number = create_or_update_record(input_data=input_data)
                message_one = 'Your request was successfully submitted for processing. To view the status, use the Reference ID'
                message_two = '{} : {}'.format(message_one, reference_number)
                message_three = 'window.open("{}","_parent");'.format('/financial-analysis-report')
                res = 'alert("{}");'.format(message_two)
                res = '{}{}'.format(res, message_three)
                return res
    raise PreventUpdate


### Validation
@app.callback(Output('valid_scenario_id', 'children'),
              [Input('datatable-upload', 'contents')],
              [State("scenario_id", "value")])
def validate_input_fields(contents, scenario_id):
    print('validate_input_fields ...', scenario_id)
    if contents is None:
        raise PreventUpdate
    else:
        pass
    if not scenario_id:
        return "Scenario can't be an empty value."


@app.callback(Output("datatable", "css"), Input("datatable", "derived_virtual_data"))
def style_export_button(data):
    if data == [] or data == [{}]:
        return [{"selector": ".export", "rule": "display:none"}]
    else:
        return [{"selector": ".export", "rule": "display:block"}]


@app.callback(Output('upload_file', 'style'), Output('scenario_id', 'style'),
              [Input('document_id', 'value')])
def toggle_upload_option(document_id):
    print('toggle_upload_option ....')
    print('document_id ===', document_id)
    if document_id is None or document_id <= 0:
        return {'display': 'block'}, {'display': 'block'}
    else:
        return {'pointer-events': 'none', 'display': 'none'}, {'pointer-events': 'none'}


@app.callback(Output('bar-scratter-graph', 'figure'),
              Output('datatable', 'data'),
              Output('avg_price_change_perc', 'value'),
              [Input('society_approval_rate_perc', 'value'),
               Input('scenario_id', 'value'),
               Input('document_id', 'value'),
               Input('datatable-upload', 'contents'),
               Input('datatable-upload', 'filename'),
               Input('filter_perc', 'value')])
def update_datatable(society_approval_rate_perc, scenario_id, document_id, contents, filename, filter_perc):
    print('update_datatable ...', scenario_id)
    print('update_datatable document_id ...', document_id)
    fig_layout = {}
    if not scenario_id:
        print('yes....')
    else:
        print('no ...')
    df = pd.DataFrame()
    if document_id > 0 and contents is None:
        df = get_rate_analysis_dataframe(document_id=document_id)
        fig_layout = prepare_graph(dataframe=df, filter_perc=filter_perc)
    elif contents is None and document_id == 0:
        return fig_layout, [{}], 0.00
    else:
        if not scenario_id:
            return fig_layout, [{}], 0.00
        file_data = {'contents': contents,
                     'filename': filename,
                     }
        df = parse_contents(file_data=file_data)
        fig_layout = prepare_graph(dataframe=df, filter_perc=filter_perc)
    data_table, average_prie_increase = prepare_pivot(dataframe=df,
                                                      society_approval_rate_perc=society_approval_rate_perc,
                                                      filter_perc=filter_perc)
    print('----end-------')
    if not data_table.empty:
        return fig_layout, data_table.to_dict('records'), average_prie_increase
    return fig_layout, [{}], 0.00
