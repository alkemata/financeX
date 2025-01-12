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
from dash.dependencies import Input, Output, State
from datetime import datetime, timedelta
import plotly.express as px

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


def create_dash_app(flask_server):
    global displayed_month
    appdash = dash.Dash(__name__,  server=flask_server,url_base_pathname='/dashboard/', external_stylesheets=[dbc.themes.BOOTSTRAP])
    df=functions.load_data('processed.csv')
    if df==0:
        return appdash
    last_update=df['Buchungsdatum'].max()
    year=df['Buchungsdatum'].dt.year.max()
    current_year=year
    current_month=df['Month'].max()
    displayed_month=current_month


#============== navbar layout
    navbar_layout = html.Div([
    dcc.Location(id='url', refresh=False),  # This tracks the current page location

    # Navbar
    html.Div([
        dcc.Link('Dashboard', href='/dashboard/',refresh=True),
        ' | ',
        dcc.Link('Année', href='/year/',refresh=True),
        ' | ',
        dcc.Link('Edit', href='/edit/',refresh=True),
    ], style={'padding': '10px', 'fontSize': '20px'}),

    # Content will be displayed here based on URL
    html.Div(id='page-content')
    ])

    param_layout=html.Div(
            id='div1',
            children=[
                dbc.Card(
                    dbc.CardBody([
                        html.H4("Date Information", className="card-title"),
                        html.P(f"Date actuelle: {datetime.now().strftime('%d-%m-%Y')}", className="card-text"),
                        html.P(f"Dernière mise à jour: {last_update.strftime('%d-%m-%Y')}", className="card-text")
                    ]),
                style={'margin-bottom': '10px', 'padding': '10px', 'border': '1px solid #ddd'}
                )
            ]
        )

    def get_month_data(df,month,year):
         
        # Filter DataFrame for last month
        mask_fix = (df['Month'] == month) & (df['Betrag']<0) &(df['Notiz']=='-')
        month_df_fix = df.loc[mask_fix]

        # Group by day and sum amounts
        daily_sum_fix = month_df_fix.groupby(month_df_fix['Buchungsdatum'].dt.day)['Betrag'].sum().reset_index()
        daily_sum_fix['Notiz']='Variable'
        mask_nonfix = (df['Month'] == month) & (df['Betrag']<0) &(df['Notiz']!='-')
        month_df_nonfix = df.loc[mask_nonfix]
        
        # Group by day and sum amounts
        daily_sum_nonfix = month_df_nonfix.groupby(month_df_nonfix['Buchungsdatum'].dt.day)['Betrag'].sum().reset_index()   
        daily_sum_nonfix['Notiz']='Fixe'
        daily_sum= pd.concat([daily_sum_fix, daily_sum_nonfix], ignore_index=True)   
        daily_sum.rename(columns={'Buchungsdatum': 'day', 'Betrag': 'total_amount'}, inplace=True)        
        return daily_sum


    def create_bar_chart(daily_sum, month,year):
        fig = px.bar(daily_sum,x='day',y='total_amount',color='Notiz',title='Dépenses par jour')
        
        fig.update_layout(
            title=f'Dépense pour le mois numéro {month}',
            xaxis_title='Jour',
            yaxis_title='Dépenses',
            bargap=0.2,
            bargroupgap=0.1,
            autosize=True
        )     
        return fig

    daily_sum= get_month_data(df,displayed_month,year)
    bar_chart_figure = create_bar_chart(daily_sum, displayed_month,year)
    monthly_total = df[(df['Betrag']<0) & (df['Month']==displayed_month)]['Betrag'].sum()
    today = last_update
    first_day_current_month = today.replace(day=1)

#todo add average spending per day
#remove income
    style_data_conditional=[
    {
        'if': {
            'filter_query': '{Notiz} != "-"',  # Conditional for 'Notiz' column
            'column_id': 'Notiz',
        },
        'backgroundColor': 'blue',  # Grey background for the row
        'color': 'white'  # Optional: white text to make it more readable
    }
    ]

    current_spend_layout= html.Div(
            id='div2',
            children=[
                        html.Button('←', id='left-arrow', n_clicks=0),
        html.Span(id='month-display'),
        html.Button('→', id='right-arrow', n_clicks=0),
                    dbc.Card(
                    dbc.CardBody([
                        html.H2(f"Total dépenses du mois: {monthly_total:.2f}", className="card-title", style={'font-size': '2em', 'text-align': 'center'}),
                    ]),
                    style={'margin-bottom': '10px', 'padding': '10px', 'border': '1px solid #ddd'}
                ),
                dcc.Graph(
                    id='bar-chart',
                    figure=bar_chart_figure
                ),
            html.Div(
            id='div3',
            children=[
                    dash_table.DataTable(
                                id='amounts-table',
                                    style_data={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                    },
                                columns=[                         
                                     {"name": "Buchungsdatum", "id": "Buchungsdatum"},
                                    {"name": "Empfaenger", "id": "Empfaenger"},                     
                                    {"name": "Verwendungszweck", "id": "Verwendungszweck"},
                                    {"name": "Betrag", "id": "Betrag"}, 
                                    {"name": "Category", "id": "Category"},
                                    {"name": "Notiz", "id": "Notiz"},
                                     ],
                                data=[],
                                style_data_conditional=style_data_conditional,
                                style_table={'overflowX': 'auto'},
                                style_header={
                                    'backgroundColor': 'rgb(230, 230, 230)',
                                    'fontWeight': 'bold'
                                },
                                style_cell={
                                    'textAlign': 'left',
                                    'padding': '10px',
                                },
                                page_size=10,
                            )
            ],
            style={'flex': '1', 'margin-bottom': '10px', 'padding': '10px', 'border': '1px solid #ddd'}
            )
            ]
        ) 

    occurences=functions.load_occurences('occurences.csv') 
    end_of_month = last_update.replace(day=28) + pd.offsets.MonthEnd(1)
    filtered_occ = occurences[(occurences['date'] >= last_update) & (occurences['date'] <= end_of_month)]

    plan_layout=html.Div([
        html.H2('Versements restant à faire ce mois-ci'),

        dash_table.DataTable(
            id='datatable',
            columns=[{'name': i, 'id': i} for i in filtered_occ.columns],
            data=filtered_occ.to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_data_conditional=[
                {
                    'if': {'column_id': 'amount'},
                    'width': '100px'
                },
                {
                    'if': {'column_id': 'description'},
                    'width': '300px'
                },
                {
                    'if': {'column_id': 'date'},
                    'width': '150px'
                }
            ],
            style_cell={'textAlign': 'left'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            editable=True,
            row_deletable=True,
            filter_action='native',
            sort_action='native',
            page_action='native',
            page_current=0,
            page_size=10,
            style_as_list_view=True
        )
    ])


    # Define callback to update the table based on the selected bar
    @appdash.callback(
        Output('amounts-table', 'data'),
        Input('bar-chart', 'clickData'),
    )
    def update_table(clickData):
        if clickData is None:
            return []
        print('updating table')
        # Get the selected date from the bar chart
        selected_date = clickData['points'][0]['x']
        today = last_update
        first_day_current_month = today.replace(day=1)
        last_day_last_month = last_update
        first_day_last_month = first_day_current_month
        # Filter the DataFrame for the selected date
        mask =  (df['Month'] == displayed_month)
        last_month_df = df.loc[mask]
        selected_data = last_month_df[last_month_df['Buchungsdatum'].dt.day.astype(int) == selected_date]
        selected_data=selected_data[["Buchungsdatum", "Empfaenger","Verwendungszweck","Betrag","Category","Notiz"]]
 
        return selected_data.to_dict('records')


    def account_saldo():
        df1=df[(df['Konto']=='{postbank_account}') & (df['Month']==displayed_month)][['Buchungsdatum','Saldo']]
        df2=df[(df['Konto']=='{commerzbank_account}') & (df['Month']==displayed_month)][['Buchungsdatum','Saldo']]

        fig1 = px.line(df1, x='Buchungsdatum', y='Saldo', title='Saldo Evolution - Postbank',markers=True)

        # Create the second graph
        fig2 = px.line(df2, x='Buchungsdatum', y='Saldo', title='Saldo Evolution - Commerzbank', markers=True)
        return fig1, fig2

    fig1, fig2=account_saldo()
    # Define the layout of the app
    saldo_layout = html.Div(children=[
        html.Div(children=[
            dcc.Graph(
                id='graph1',
                figure=fig1
            )
        ]), 

        html.Div(children=[
            dcc.Graph(
                id='graph2',
                figure=fig2
            )
        ])
    ]) 

    @appdash.callback(
        [Output('month-display', 'children'),
        Output('left-arrow', 'style'),
        Output('right-arrow', 'style'),
        Output('bar-chart','figure'),
        Output('graph1','figure'),
        Output('graph2','figure')
        ],
        [Input('left-arrow', 'n_clicks'),
        Input('right-arrow', 'n_clicks')],
        [State('month-display', 'children')]
        
    )
    def update_month(left_clicks, right_clicks, toto):
        global displayed_month
        # Initialize variables
        # Adjust month based on arrow clicks
        if left_clicks > right_clicks:
            if displayed_month == 1:
                displayed_month = 12
            else:
                displayed_month -= 1
        elif right_clicks > left_clicks:
            if displayed_month == 12:
                displayed_month = 1

            else:
                displayed_month += 1


        # Control visibility of the arrows
        left_style = {}
        right_style = {}
        
        if displayed_month == 1:
            left_style = {'visibility': 'hidden'}
        if displayed_month == current_month:
            right_style = {'visibility': 'hidden'}

        daily_sum= get_month_data(df,displayed_month,year)
        fig=create_bar_chart(daily_sum,displayed_month,year)
        fig1, fig2=account_saldo()
        return '', left_style, right_style, fig, fig1, fig2     
        



    def layout_main():
        layout=html.Div(
        style={'display': 'flex', 'flex-direction': 'column', 'padding': '10px'},  # Makes layout responsive
        children=[navbar_layout,param_layout,current_spend_layout,plan_layout,saldo_layout])
        return layout

    appdash.layout=layout_main()
    return appdash





