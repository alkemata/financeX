import pandas as pd
import logging
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import dash_bootstrap_components as dbc
from dash import html
from dash import dcc, html, dash_table
from FinanceX import functions as functions
import dash
from datetime import datetime, timedelta
import calendar
import plotly.graph_objs as go
import numpy as np 
from dash.dependencies import Input, Output
from datetime import datetime, timedelta
import plotly.express as px
import dash_ag_grid as dag

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def create_dash_app(flask_server):
    appedit= dash.Dash(__name__,  server=flask_server,url_base_pathname='/edit/', external_stylesheets=[dbc.themes.BOOTSTRAP])
    df=functions.load_data('processed.csv')
    
#============== navbar layout
    navbar_layout = html.Div([
    dcc.Location(id='url', refresh=False),  # This tracks the current page location

    # Navbar
    html.Div([
        dcc.Link('Home', href='/dashboard/',refresh=True),
        ' | ',
        dcc.Link('Year', href='/year/',refresh=True),
        ' | ',
        dcc.Link('Edit', href='/edit/',refresh=True),
    ], style={'padding': '10px', 'fontSize': '20px'}),

    # Content will be displayed here based on URL
    html.Div(id='page-content')
    ])

    getRowStyle = {
        "styleConditions": [
            {
                "condition": "params.data.Betrag > 0",
                "style": {"backgroundColor": "lightcoral"},
            },
            {
                "condition": "params.data.Kategorie == 'Umbuchung'",
                "style": {"backgroundColor": "grey"}
            },
                        {
                "condition": "params.data.Notiz != '-'",
                "style": {"backgroundColor": "sandybrown"}
            },
        ],
        "defaultStyle": {"backgroundColor": "white", "color": "black"}
    }



    column_defs = [{"headerName": col, "field": col, "resizable": True} for col in df.columns]

    layout_list_global= html.Div(
        children=[
            html.H1("Yearly view"),
            dcc.Input(id='filter-input', type='text', placeholder='Enter Notiz for the selection'),
            html.Button('ADD', id='filter-button', n_clicks=0),
                      
            dag.AgGrid(
                id='table',
                style={"height": 600, "width": "100%"},
                columnDefs=column_defs,
                rowData=df.to_dict('records'),
                defaultColDef={"resizable": True,'filter': True, 'sortable': True},  # Make all columns resizable
                getRowStyle=getRowStyle,
            ),             
        ])

    def layout_main():
        layout=html.Div(
        style={'display': 'flex', 'flex-direction': 'column', 'padding': '10px'},  # Makes layout responsive
        children=[navbar_layout,layout_list_global])
        return layout

    appedit.layout=layout_main()
    return appedit