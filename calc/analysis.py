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
from django.shortcuts import render,redirect
import dash_bootstrap_components as dbc
from dash import dcc, html, callback_context, dash_table as dt
from dash.dash_table import DataTable, FormatTemplate
from dash.dash_table.Format import Format, Group, Scheme, Symbol, Sign
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from django_plotly_dash import DjangoDash
import logging
logger = logging.getLogger(__file__)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',
                        {'href':'http://127.0.0.1:8000/static/calc/css/style.css', 'rel': 'stylesheet'},
                        #dbc.themes.BOOTSTRAP
                        ]
app = DjangoDash('AnalysisApp', external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

colors = {
    'background': '#ffffff',
    'text': '#212529'
}

alert = dbc.Alert("Testing ... ", color="danger", dismissable=True)

app.layout = html.Div([
    html.Div([
        html.Div([
            dcc.Input(id='user_id', persistence=False, value=0)],style={'display':'none'}),
        html.Div([
            dcc.Input(id='calculator_id', persistence=False, value=0)],style={'display':'none'}),
        html.Div([
            dcc.Input(id='analysis_id', persistence=False, value=0)],style={'display':'none'}),
        html.Div([
            html.P('Select Scenario', className='fix_label',
                        style={'color': colors['text']}),
            dcc.Dropdown(id='scenario_id',
                         options=[],
                         value='',
                         style={'textAlign': 'left', 'color': 'black',
                                'height': '36px', 'width': '290px'},
                         className='dcc_compon'),
        ], className='one-third column', id='title13', style={'margin-left':'0'}),
        html.Div([
            dcc.Upload(
                id='datatable-upload',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                accept=".csv",
                multiple=False,
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed',
                    'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px',
                    'display': 'block'
                },
            ),
        ], className='one-third column', id='upload_file', style={'margin-left':'0','width': '50%'}),
        dcc.ConfirmDialog(
            id='confirm-danger',
            message='Are you sure you want to continue?',
        ),
        html.Div(id="the_alert",children=[]),
        html.Div([
            html.P('Filter Percentage (%)', className='fix_label',
                   style={'color': colors['text']}),
            dcc.Input(id='filter_perc', type='number', value=20.00,
                      style={'height': '36px', 'width': '290px'}),
        ], className='one-third column', id='title4', style={'margin-left':'0'}),
        html.Div([
            html.P('Society Approval Rate (%)', className='fix_label',
                   style={'color': colors['text']}),
            dcc.Input(id='society_approval_rate_perc', type='number', value=50.00,
                      style={'height': '36px', 'width': '290px'}),
        ], className='one-third column', id='title4', style={'margin-left':'0'}),
        html.Div([
            html.P('Average Price Increase (%)', className='fix_label',
                   style={'color': colors['text']}),
            dcc.Input(id='avg_price_change_perc', type='number', value=0.00, #readOnly=1,
                      style={'height': '36px', 'width': '290px', 'background': '#f9f8f8'},
                      ),
        ], className='one-third column', id='title6', style={'margin-left':'0'}),
        html.Div([
            html.P('Combined average price increase (Gold + Hybrid)',
                   className='fix_label', style={'color': colors['text'],'display': 'none'},
                   ),
            dcc.Input(id='comb_avg_price_increase', type='text', value="0.00%",
                      style={'height': '36px', 'width': '290px'},
                      ),
            ], className='one-third column', id='title7', style={'margin-left':'0','display': 'none'}),
        ], style={'display': 'flex', 'flex-wrap':'wrap', 'justify-content':'start',
                  'align-items':'center', 'row-gap':'30px', 'gap': '30px', 'margin-bottom':'30px'}),
        html.Div([
            html.Button(id='submit-button-state', children="Submit", style={'float' : 'right','background': '#1f2c56',
                                                                            'color' : '#f5a004','font-size' : '14px',
                                                                            'margin-bottom' : '12px','margin-right' : '6px',
                                                                            'font-family': 'sans-serif','font-weight' : '600'}),
            ]),
    html.Div(id='output-state', style={'display': 'block'}),
    html.Div([
        html.Div([
            dt.DataTable(id='datatable',
                         columns=[
                             {"name": ["", "APC change %"], "id": "APC change %"},
                             {"name": ["N-Society Owned", "Number of journals"],
                                        "id": "N-Number of Journals"},
                             {"name": ["N-Society Owned", "Revenue change $"],
                                        "id": "N-Revenue change",
                                        "type" : "numeric",
                                        'format': Format(
                                          precision=2,
                                          scheme=Scheme.fixed,
                                          symbol=Symbol.yes,
                                          symbol_prefix="{} ".format(Symbol.yes),
                                          group = ','
                                        )},
                             {"name": ["J-Joint Owned", "Number of journals"], "id": "J-Number of Journals"},
                             {"name": ["J-Joint Owned", "Revenue change $"],
                                        "id": "J-Revenue change",
                                        "type" : "numeric",
                                        'format': Format(
                                          precision=2,
                                          scheme=Scheme.fixed,
                                          symbol=Symbol.yes,
                                          symbol_prefix="{} ".format(Symbol.yes),
                                          group = ','
                                        )},
                             {"name": ["O-Proprietary Owned", "Number of journals"], "id": "O-Number of Journals"},
                             {"name": ["O-Proprietary Owned", "Revenue change $"],
                                        "id": "O-Revenue change",
                                        "type" : "numeric",
                                        'format': Format(
                                          precision=2,
                                          scheme=Scheme.fixed,
                                          symbol=Symbol.yes,
                                          symbol_prefix="{} ".format(Symbol.yes),
                                          group = ','
                                        )},
                             {"name": ["", "Total Number of Journals $"], "id": "Total-Number of Journals"},
                             {"name": ["", "Total Revenue change $"],
                                        "id": "Total-Revenue change",
                                        "type" : "numeric",
                                        'format': Format(
                                          precision=2,
                                          scheme=Scheme.fixed,
                                          symbol=Symbol.yes,
                                          symbol_prefix="{} ".format(Symbol.yes),
                                          group = ','
                                        )},
                         ],
                         virtualization=True,
                         # export_format="csv",
                         style_cell={'textAlign': 'center',
                                     'min-width': '100px',
                                     'backgroundColor': '#1f2c56',
                                     'color': '#FEFEFE',
                                     'border-bottom': '0.01rem solid #19AAE1',
                                     'font-size': '15px',
                                     'height': '40px'},
                         style_header={'backgroundColor': '#1f2c56',
                                       'fontWeight': 'bold',
                                       'font': 'Lato, sans-serif',
                                       'color': 'orange',
                                       'border': '#1f2c56',
                                       'font-size': '18px'},
                         style_as_list_view=True,
                         style_data={'styleOverflow': 'hidden',
                                     'color': 'white', 'font-size': '14px',
                                     'font-weight': '520',
                                     'font-family': 'sans-serif'},
                         fixed_rows={'headers': True},
                         sort_action='native',
                         page_size=20,
                         style_header_conditional=[
                             {'if': {'column_id': 'Customer ID', 'header_index': 0},
                              'text-align': '-webkit-center'},
                             {'if': {'column_id': 'Customer Name',
                                     'header_index': 0}, 'text-align': '-webkit-center'},
                             {'font-size': '16px',
                              'font-weight': '580',
                              'font-family': 'sans-serif'}
                         ],
                         merge_duplicate_headers=True,
                         sort_mode='multi')
        ], className='create_container2'),
    ], className='row flex-display')
], id='mainContainer', style={'display': 'flex', 'flexDirection': 'column', 'padding':'15px'})

UPLOAD_DIRECTORY = 'C:\\Users\\Lenovo\\Documents\\GitHub\\wileydash\\scripts\\2022.03.09\\Calc_1'

def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))

def get_file_rename(filename):
    filename_str = os.path.splitext(filename)[0]
    extension = os.path.splitext(filename)[1]
    new_filename = filename_str + str(uuid.uuid4()) + '.csv'
    extension = os.path.splitext(filename)[1]
    return new_filename

def convert_dataframe_to_file(dataframe, filename):
    filepath = os.path.join(UPLOAD_DIRECTORY,filename)
    if not os.path.exists(filepath):
        print('\n mkdir')
    else:
        filename = get_file_rename(filename)
    new_filepath = os.path.join(UPLOAD_DIRECTORY,filename)
    df1 = dataframe.to_csv(new_filepath, index=False)
    return new_filepath

@transaction.atomic()
def create_record(save=True,**kwargs):
    input_data = kwargs.get('input_data',False)
    print('\n input_data ====',input_data)
    calculator_obj = CalculatorMaster.objects.get(pk=int(input_data.get('calculator_id')))
    scenario_obj = ScenarioMaster.objects.get(pk=int(input_data.get('scenario_id')))
    parent_data = {'calculator_id' : calculator_obj,
                   'scenario_id' : scenario_obj,
                   'filter_perc' : 0.00,
                   'society_approval_rate_perc' : 0.00,
                   'avg_price_change_perc' : 0.00,
                   #'document_id' : 1,
                   'status' : 'pending',
                   'remarks' : 'testing auto',
                   'description' : 'testing auto'
                   }
    # document_rec = Document.objects.create(**parent_data)
    rate_analysis_rec = RateAnalysis.objects.create(**parent_data)
    parent_sp = transaction.savepoint()
    line_data = {'ownership_structure' : 'N-Joined',
                 'apc_change_perc' : '1-2%',
                 'journal_count' : 4,
                 'revenue_change' : 5410.00,
                 'rate_analysis_id': rate_analysis_rec
    }
    rate_analysis_detailone_rec = RateAnalysisDetails.objects.create(**line_data)
    if save:
        transaction.savepoint_commit(parent_sp)
    else:
        transaction.savepoint_rollback(parent_sp)
    line_data['apc_change_perc'] = '3-4%'
    line_data['journal_count'] = 2
    line_data['revenue_change'] = 3050.50
    rate_analysis_detailtwo_rec = RateAnalysisDetails.objects.create(**line_data)
    rate_analysis_rec.save()
    rate_analysis_detailone_rec.save()
    rate_analysis_detailtwo_rec.save()
    return True

def parse_contents(**kwargs): # contents, filename, action = None):
    file_data = kwargs.get('file_data',False)
    contents = file_data and file_data.get('contents', False)
    filename = file_data and file_data.get('filename', False)
    action = file_data and file_data.get('action', False)
    if contents and filename:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
            return df
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
            # df1 = df.to_excel(os.path.join(UPLOAD_DIRECTORY,filename), index=False)
            return df
        # if action:
        #     if filename is not None and contents is not None:
        #         for name, data in zip(filename, contents):
        #             save_file(name, data)

def prepare_pivot(**kwargs):
    dataframe = kwargs.get('dataframe',False)
    society_approval_rate_perc = kwargs.get('society_approval_rate_perc',False)
    filter_perc = kwargs.get('filter_perc',False)
    columns = ['Journal Code', 'Journal', 'Percentage Change', 'Ownership Structure',
               '% category', 'Revenue change']
    try:
        dataframe = pd.DataFrame(dataframe, columns=columns)
        dataframe_filter = dataframe.loc[dataframe['Percentage Change'] <= (filter_perc / 100)]
        table = pd.pivot_table(data=dataframe_filter,
                               values=['Journal Code', 'Revenue change', 'Percentage Change'],
                               index=['% category'],
                               columns=['Ownership Structure'],
                               aggfunc={'Journal Code': len,
                                        'Revenue change': np.sum,
                                        'Percentage Change': np.sum},
                               margins=True, margins_name='Total').\
                               reset_index().rename(columns={'Journal Code': 'Number of Journals',
                                                             '% category': 'APC change %'})
        print(table)
        table.columns = list(map( lambda x: '-'.join([x[1].split('-')[0], x[0]])
                                                if x[1].find('-') != -1  else '-'.join([x[1], x[0]])
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
        # print("----1------")
        # print(table)
        average_prie_increase = (dataframe_filter['Percentage Change'].mean()) * (1 - society_approval_rate_perc)

        table = prepare_approval_data(dataframe=table, society_approval_rate_perc=society_approval_rate_perc)

        # print("----3------")
        # print(data_table)
    except Exception as e:
        print('\n Exception args ... ',e.args)
        return pd.DataFrame()
    return table,average_prie_increase

def prepare_approval_data(**kwargs):
    dataframe = kwargs.get('dataframe', False)
    approval_rate = kwargs.get('society_approval_rate_perc', False)
    # print(dataframe)

    df_zero = {}
    for col in dataframe.columns:
        if col.find('-') != -1 and  col.split('-')[0] == "N":
            dataframe[col] = dataframe[col].apply(lambda x: (x * approval_rate) / 100)
            if col.split('-')[1] == "Number of Journals":
                df_zero[col] = dataframe.drop(dataframe.index[-1]).loc[:,col].sum()


    if '0%' not in dataframe['APC change %']:
        dataframe.loc[-1] = [0] * len(dataframe.columns)
        dataframe.index = dataframe.index + 1
        dataframe.sort_index(inplace=True)
        dataframe['APC change %'][0] = "0%"
        for key, value in df_zero.items():
            dataframe[key][0] = value
            dataframe[key] = dataframe.apply(lambda x: dataframe.drop(dataframe.index[-1]).loc[:,key].sum()
                                            if x['APC change %'] == "Total" else x[key], axis=1)

    for col in dataframe.columns:
        if col.find('Total') != -1 :
            dataframe[col] = dataframe[[dif_col for dif_col in dataframe.columns
                                        if dif_col.find('-') != -1 and dif_col.split('-')[1] == col.split('-')[1]
                                        and dif_col.find('Total') == -1]].sum(axis=1)

    # print(dataframe)
    return dataframe


def get_calculator_directory(**kwargs):
    print ('get calc dir...........',kwargs)
    calculator_id = kwargs.get('calculator_id',0)
    user_id = kwargs.get('user_id',0)
    calculator_directory = False
    if calculator_id <= 0:
        profile_obj = Profile.objects.get(user=int(user_id))
        calculator_id = profile_obj.calculator_id and profile_obj.calculator_id.id or calculator_id
    if calculator_id > 0:
        calculator_obj = CalculatorMaster.objects.get(pk=int(calculator_id))
        calculator_directory = calculator_obj and calculator_obj.directory_name or calculator_directory
    return calculator_directory

def update_rate_analysis(**kwargs):
    # print ('update rate analysis =====',kwargs)
    filelocation = settings.DATA_FILE_DIR + '/scripts/'
    analysis_data = {'calculator_id'                : None,
                     'scenario_id'                  : None,
                     'filter_perc'                  : 0.00,
                     'society_approval_rate_perc'   : 0.00,
                     'avg_price_change_perc'        : 0.00,
                     'document_id'                  : None,
                     'status'                       : 'pending',
                     'remarks'                      : None,
                     'description'                  : None
                     }
    if kwargs.get('input_data',False):
        input_data = kwargs.get('input_data')
        # calculator_directory = get_calculator_directory(user_id = input_data.get('user_id',0), calculator_id = input_data.get('calculator_id',0))
        # if calculator_directory:
        filelocation = get_filelocation(**kwargs)
        # print('\n filelocation ======',filelocation)


@app.callback(Output('scenario_id', 'options'),
              Output('scenario_id', 'value'),
              [Input('user_id', 'value')])
def update_scenario(user_id):
    scenario_obj1 = ScenarioMaster.objects.values('pk', 'name')
    scenario_list1 = scenario_obj1 and list(scenario_obj1) or []
    if scenario_obj1:
        return [{'label': i.get('name'), 'value': i.get('pk')} for i in scenario_list1], scenario_list1[0].get('pk')
    return [{}], ''

# @app.callback(#Output('confirm-danger', 'displayed'),
#               Output('the_alert', 'children'),
#               Input('submit-button-state', 'n_clicks'))
# def display_confirm(n_clicks):
#     if n_clicks:
#         return alert
#     return False

@app.callback(Output(component_id='output-state', component_property='children'),
              Input('submit-button-state', 'n_clicks'),
              Input('scenario_id', 'value'),
              State('user_id', 'value'),
              State('calculator_id', 'value'),
              State('society_approval_rate_perc', 'value'),
              State('avg_price_change_perc', 'value'),
              State('datatable', 'data'),
              State('datatable-upload', 'filename')
               )
def update_output(submit_btn, scenario_id, user_id, calculator_id, society_approval_rate_perc, avg_price_change_perc, datatable, filename):
    # print ('update output children ====',submit_btn)
    # print ('update output user_id ====',user_id)
    # print ('update output scenario_id ====',scenario_id)
    # print ('update output calculator_id ====',calculator_id)
    # print ('update output society_approval_rate_perc ====',society_approval_rate_perc)
    # print ('update output avg_price_change_perc ====',avg_price_change_perc)
    # print ('update output datatable ====',datatable)
    # print ('update output filename ====',filename)
    input_data = {'scenario_id'                 : scenario_id,
                  'calculator_id'               : calculator_id,
                  'user_id'                     : user_id,
                  'society_approval_rate_perc'  : society_approval_rate_perc,
                  'avg_price_change_perc'       : avg_price_change_perc,
                  'datatable'                   : datatable,
                  'filename'                    : filename
                  }
    update_rate_analysis(input_data = input_data)
    if scenario_id != 0 and society_approval_rate_perc != 0 and avg_price_change_perc != 0 and submit_btn and datatable != [[{}], []]:
        print ('\n yes')
        # x = create_record(input_data = input_data)
        return 'Success'
    # return u'''
    #     The Button has been pressed {} times,
    #     Input 1 is "{}",
    #     and Input 2 is "{}"
    # '''.format(n_clicks, input1, input2)

# @app.callback(Output('my_datatable2', 'data'),
#               [Input('user_id', 'value'), Input('calculator_id', 'value')])
# def load_datatable(user_id, calculator_id):
#     context = {}
#     calculator_directory = False
#     if calculator_id <= 0:
#         profile_obj = Profile.objects.get(user=int(user_id))
#         calculator_id = profile_obj.calculator_id and profile_obj.calculator_id.id or calculator_id
#     if calculator_id > 0:
#         calculator_obj = CalculatorMaster.objects.get(pk=int(calculator_id))
#         calculator_directory = calculator_obj and calculator_obj.directory_name or calculator_directory
#     if calculator_directory:
#         context['calculator_directory'] = calculator_directory
#         context['filter_file'] = ['Journal_Database']
#         filedataframe = get_filedataframe(**context)
#         journal_database = filedataframe.get('journal_database', False)
#         data_table = prepare_pivot(dataframe=journal_database)
#         return data_table.to_dict('records') #,'17.00%'

# @app.callback(Output('datatable', 'data'),
#               #Output('comb_avg_price_increase', 'value'),
#               [Input('society_approval_rate_perc', 'value'), Input('scenario_id', 'value'),
#                Input('datatable-upload', 'contents'),Input('datatable-upload', 'filename')])
# def update_datatable(society_approval_rate_perc, scenario_id, contents, filename):
#     # print('scenario_id=====',scenario_id)
#     if contents is None:
#         return [{}], []
#     file_data = { 'contents' : contents,
#                   'filename': filename,
#                   }
#     df = parse_contents(file_data = file_data)
#     data_table = prepare_pivot(dataframe=df,society_approval_rate_perc=society_approval_rate_perc)
#     if not data_table.empty:
#         return data_table.to_dict('records') #,'17.00%'
#     return [{}]


@app.callback(Output('datatable', 'data'),
              Output('avg_price_change_perc','data'),
              Input('user_id', 'value'), Input('calculator_id', 'value'),
              Input('society_approval_rate_perc', 'value'),
              Input('filter_perc','value'))
def load_datatable(user_id, calculator_id,society_approval_rate_perc,filter_perc):
    context = {}
    calculator_directory = False
    print(user_id,calculator_id)
    if calculator_id <= 0:
        profile_obj = Profile.objects.get(user=int(user_id))
        calculator_id = profile_obj.calculator_id and profile_obj.calculator_id.id or calculator_id
    if calculator_id > 0:
        calculator_obj = CalculatorMaster.objects.get(pk=int(calculator_id))
        calculator_directory = calculator_obj and calculator_obj.directory_name or calculator_directory
    if calculator_directory:
        context['calculator_directory'] = calculator_directory
        context['filter_file'] = ['Journal_Database']
        filedataframe = get_filedataframe(**context)
        journal_database = filedataframe.get('journal_database', False)
        # get_filelocation(calculator_directory=calculator_directory)
        data_table,average_prie_increase = prepare_pivot(dataframe=journal_database,society_approval_rate_perc=society_approval_rate_perc,filter_perc=filter_perc)
        return data_table.to_dict('records'),average_prie_increase