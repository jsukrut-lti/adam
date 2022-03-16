import sys,os
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
import visdcc
import logging
import plotly.express as px
logger = logging.getLogger(__file__)

app = DjangoDash('AnalysisApp01')

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

fig.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)

app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[


    dcc.Graph(
        id='example-graph-2',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)