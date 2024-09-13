import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import numpy as np

# Load data from CSV files
df1 = pd.read_csv('result1.csv', delimiter=';')
df2 = pd.read_csv('result2.csv', delimiter=';')

GRID_LIMIT = 150

def preprocess(df):
    df['time'] = df['time'].astype(int)
    df['vehicle'] = df['vehicle'].str.replace(',', '.').astype(float)
    df = df.dropna(subset=['vehicle'])
    df['vehicle'] = df['vehicle'].astype(int)
    df['cp_charging_rate'] = df['cp_charging_rate'].str.replace(',', '.').astype(float)
    df['cp_target_power'] = df['cp_target_power'].str.replace(',', '.').astype(float)
    df['vehicle_soc'] = df['vehicle_soc'].str.replace(',', '.').astype(float)
    df['vehicle_charge'] = df['vehicle_charge'].str.replace(',', '.').astype(float)
    df['vehicle_capacity'] = df['vehicle_capacity'].str.replace(',', '.').astype(float)
    df['cp_charge_increment'] = df['cp_charge_increment'].str.replace(',', '.').astype(float)
    df['time_minute'] = df['time'] / 60
    df['time_of_day'] = pd.to_datetime(df['time'], unit='s', utc=True).map(lambda x: x.tz_convert("Europe/Berlin"))
    return df

df1 = preprocess(df1)
df2 = preprocess(df2)

def calculate_kpis(df):
    total_energy_used = df['cp_charge_increment'].sum()
    cars_charged = df[df['vehicle_charge'] > 0]['vehicle'].nunique()
    cars_not_charged = df[df['vehicle_charge'] == 0]['vehicle'].nunique()

    # Filter cars that have the last 3 entries with cp_charge_increment, cp_charging_rate, and cp_target_power as zero
    last_3_entries = df.groupby('vehicle').tail(3)
    condition = (last_3_entries['cp_charge_increment'] == 0) & (last_3_entries['cp_charging_rate'] == 0) & (last_3_entries['cp_target_power'] == 0)
    vehicles_stopped_charging = last_3_entries[condition].groupby('vehicle').filter(lambda x: len(x) == 3)['vehicle'].unique()

    df_stopped_charging = df[df['vehicle'].isin(vehicles_stopped_charging)]
    avg_soc_ac = df_stopped_charging.groupby('vehicle').tail(1)['vehicle_soc'].mean()
    median_soc = df_stopped_charging.groupby('vehicle').tail(1)['vehicle_soc'].median()

    first_entries = df.groupby('vehicle').head(1)
    avg_soc_bc = first_entries['vehicle_soc'].mean()

    return total_energy_used, cars_charged, cars_not_charged, avg_soc_ac, median_soc, avg_soc_bc

app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

# Base
app.layout = html.Div([
    html.Div([
        dcc.Link('Dashboard', href='/Dash', className='nav-link', id='link-dash'),
        dcc.Link('Charging Infrastructure', href='/charging-infrastructure', className='nav-link', id='link-charging'),
        dcc.Link('Cars', href='/cars', className='nav-link', id='link-cars'),
        dcc.Link('Charging Station', href='/charging-station', className='nav-link', id='link-station'),
    ], className='div-header-bar'),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content', style={'display': 'flex'})
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/charging-infrastructure':
        return html.Div([
            charging_infrastructure_layout,
        ], style={'width': '100%'})
    elif pathname == '/cars':
        return html.Div([
            cars_layout,
        ], style={'width': '100%'})
    elif pathname == '/charging-station':
        return html.Div([
            charging_station_layout,
        ], style={'width': '100%'})
    else:
        return html.Div([
            dashboard_layout
        ], style={'width': '100%'})


@app.callback(
    [Output('link-dash', 'className'),
     Output('link-charging', 'className'),
     Output('link-cars', 'className'),
     Output('link-station', 'className')],
    [Input('url', 'pathname')]
)
def update_active_link(pathname):
    # Define the default classes
    class_dash = 'nav-link'
    class_charging = 'nav-link'
    class_cars = 'nav-link'
    class_station = 'nav-link'

    # Update the class of the active link
    if pathname == '/charging-infrastructure':
        class_charging = 'nav-link active'
    elif pathname == '/cars':
        class_cars = 'nav-link active'
    elif pathname == '/charging-station':
        class_station = 'nav-link active'
    else:
        class_dash = 'nav-link active'

    return class_dash, class_charging, class_cars, class_station

# Dashboard Layout
dashboard_layout = html.Div(
    children=[
    html.H1("Dashboard"),
    html.Div(id='kpis', className='div-table'),
])

# Charging Infrastructure Layout
charging_infrastructure_layout = html.Div(
    children=[
    html.H1("Charging Infrastructure"),
    html.Div(children=[
        html.Div(children=[
            html.H3('Selected Dataset'),
            dcc.Checklist(
                id='data-toggle-infrastructure',
                options=[
                    {'label': 'Dataset 1', 'value': 'df1'},
                    {'label': 'Dataset 2', 'value': 'df2'}
                ],
                value=['df1', 'df2'],
                labelStyle={'display': 'block', 'margin-bottom': '10px', 'font-size': '18px'}
            ),
            html.Hr(style={'border': '1px solid white', 'margin-top': '20px', 'margin-bottom': '20px'}),
            html.H3('Dataset View'),
            dcc.RadioItems(
                id='view-toggle-infrastructure',
                options=[
                    {'label': 'Combined', 'value': 'combined'},
                    {'label': 'Separate', 'value': 'separate'}
                ],
                value='combined',
                labelStyle={'display': 'block', 'margin-bottom': '10px', 'font-size': '18px'}
            ),
            html.Hr(style={'border': '1px solid white', 'margin-top': '20px', 'margin-bottom': '20px'}),
            html.H3('Graph Options'),
            dcc.Checklist(
                id='graph-toggle-infrastructure',
                options=[
                    {'label': 'Total Energy Used', 'value': 'total_energy'},
                    {'label': 'CP Target Power', 'value': 'target_power'},
                    {'label': 'CP Charging Rate', 'value': 'charging_rate'},
                    {'label': 'Grid Limit', 'value': 'grid_limit'},
                    {'label': 'Cars Currently Charging', 'value': 'cars_charging'}
                ],
                value=['total_energy', 'target_power', 'charging_rate', 'grid_limit', 'cars_charging'],
                labelStyle={'display': 'block', 'margin-bottom': '10px'}
            )], className='div-user-controls'),
        html.Div(id='infrastructure-graph-container', className='div-for-charts'),
    ], style={'display': 'flex'})])

# Cars Layuot
cars_layout = html.Div(
    children=[
    html.H1("Cars"),
    html.Div(children=[
            html.Div(children=[
                html.H3('Selected Vehicle'),
                dcc.Dropdown(
                    id='car-dropdown',
                    options=[{'label': car, 'value': car} for car in df1['vehicle'].unique()],
                    value=df1['vehicle'].unique()[0],
                    className='station-dropdown'
                ),
                html.Hr(style={'border': '1px solid white', 'margin-top': '20px', 'margin-bottom': '20px'}),
                html.H3('Dataset View'),
                dcc.RadioItems(
                    id='view-toggle-cars',
                    options=[
                        {'label': 'Combined', 'value': 'combined'},
                        {'label': 'Separate', 'value': 'separate'}
                    ],
                    value='combined',
                    labelStyle={'display': 'block', 'margin-bottom': '10px', 'font-size': '18px'}
                ),
                html.Hr(style={'border': '1px solid white', 'margin-top': '20px', 'margin-bottom': '20px'}),
                html.H3('Graph Options'),
                dcc.Checklist(
                    id='graph-toggle-cars',
                    options=[
                        {'label': 'Total Energy Used', 'value': 'total_energy'},
                        {'label': 'State of Charge', 'value': 'soc'},
                        {'label': 'CP Target Power', 'value': 'target_power'},
                        {'label': 'CP Charging Rate', 'value': 'charging_rate'}
                    ],
                    value=['total_energy','soc','target_power','charging_rate'],
                    labelStyle={'display': 'block', 'margin-bottom': '10px'}
                )], className='div-user-controls'),
            html.Div(id='car-graph-container', className='div-for-charts')], style={'display': 'flex'})
    ])

# Charging Station Layout
charging_station_layout = html.Div(children=[
    html.H1("Charging Station"),
    html.Div(children=[
        html.Div(children=[
            html.H3('Selected Charging Station'),
            dcc.Dropdown(
                id='station-dropdown',
                options=[{'label': station, 'value': station} for station in sorted(df1['cp'].unique())],
                value=sorted(df1['cp'].unique())[0],
                className='station-dropdown'
            ),
            html.Hr(style={'border': '1px solid white', 'margin-top': '20px', 'margin-bottom': '20px'}),
            html.H3('Dataset View'),
            dcc.RadioItems(
                id='view-toggle-stations',
                options=[
                    {'label': 'Combined', 'value': 'combined'},
                    {'label': 'Separate', 'value': 'separate'}
                ],
                value='combined',
                labelStyle={'display': 'block', 'margin-bottom': '10px', 'font-size': '18px'}
            ),
            html.Hr(style={'border': '1px solid white', 'margin-top': '20px', 'margin-bottom': '20px'}),
            html.H3('Graph Options'),
            dcc.Checklist(
                id='graph-toggle-stations',
                options=[
#                    {'label': 'Total Energy Delivered', 'value': 'total_energy'},
                    {'label': 'Target Power over the Day', 'value': 'target_power'},
                    {'label': 'Charging Rate over the Day', 'value': 'charging_rate'}
                ],
                value=['target_power','charging_rate'],
                labelStyle={'display': 'block', 'margin-bottom': '10px'}
            )], className='div-user-controls'),
        html.Div(id='station-graph-container', className='div-for-charts')], style={'display': 'flex'})
])

base = html.Div(children=[
                      html.Div(className='row',
                               children=[
                                  html.Div(className='four columns div-user-controls',
                                           children=[
                                           html.H1('test')]),  # User
                                  html.Div(className='eight columns div-for-charts bg-grey',
                                           children=[
                                               html.H1('test')]
                               )  # Graph
                                  ])
                                ])


@app.callback(Output('kpis', 'children'),
              Input('url', 'pathname'))
def update_kpis(pathname):
    total_energy_1, cars_charged_1, cars_not_charged_1, avg_soc_ac_1, median_soc_1, avg_soc_bc_1 = calculate_kpis(df1)
    total_energy_2, cars_charged_2, cars_not_charged_2, avg_soc_ac_2, median_soc_2, avg_soc_bc_2 = calculate_kpis(df2)

    return dash_table.DataTable(
    data = [
        {'KPI': 'Total Energy Used (kWh)', 'Dataset 1': round(total_energy_1,2), 'Dataset 2': round(total_energy_2,2)},
        {'KPI': 'Cars Charged', 'Dataset 1': cars_charged_1, 'Dataset 2': cars_charged_2},
        {'KPI': 'Cars Not Charged', 'Dataset 1': cars_not_charged_1, 'Dataset 2': cars_not_charged_2},
        {'KPI': 'Average SoC before Charging', 'Dataset 1': round(avg_soc_bc_1,3), 'Dataset 2': round(avg_soc_bc_2,3)},
        {'KPI': 'Average SoC after Charging', 'Dataset 1': round(avg_soc_ac_1,4), 'Dataset 2': round(avg_soc_ac_2,4)},
#        {'KPI': 'Median SoC', 'Dataset 1': median_soc_1, 'Dataset 2': median_soc_2},
    ],
    columns = [
        {'name': 'KPI', 'id': 'KPI'},
        {'name': 'Dataset 1', 'id': 'Dataset 1'},
        {'name': 'Dataset 2', 'id': 'Dataset 2'}
    ],
    style_header = {
        'backgroundColor': 'rgb(30, 30, 30)',
        'color': 'white',
        'fontWeight': 'bold',
        'border': '1px solid black',
    },
    style_cell = {
        'backgroundColor': 'rgb(50, 50, 50)',
        'color': 'white',
        'textAlign': 'left',
        'padding': '10px',
        'border': '1px solid black',
    },
    style_data = {
        'border': '1px solid grey',
    },
    style_table = {
        'borderRadius': '5px',
        'overflow': 'hidden',
        'margin': 'auto',
    },
    style_as_list_view = True,
        style_data_conditional=[
            {
                'if': {'state': 'selected'},
                'backgroundColor': 'rgb(70, 70, 70)',
                'color': 'white'
            },
            {
                'if': {'state': 'active'},
                'backgroundColor': 'rgb(90, 90, 90)',
                'color': 'white'
            }
        ]
    )


@app.callback(Output('infrastructure-graph-container', 'children'),
              [Input('data-toggle-infrastructure', 'value'),
               Input('view-toggle-infrastructure', 'value'),
               Input('graph-toggle-infrastructure', 'value')])
def update_infrastructure_graph(data_toggle, view_toggle, graph_toggle):
    data_map = {'df1': df1, 'df2': df2}
    traces = []
    total_energy_traces = []
    charging_cars_traces = []

    def create_traces(df, dataset_name, line_style):
        trace_list = []
        if 'target_power' in graph_toggle:
            target_power = df.groupby('time_of_day')['cp_target_power'].sum()
            trace_list.append(go.Scatter(x=target_power.index, y=target_power, line_shape='hv', mode='markers+lines',
                                         name=f'{dataset_name} - CP Target Power', line=line_style))
        if 'charging_rate' in graph_toggle:
            charging_rate = df.groupby('time_of_day')['cp_charging_rate'].sum()
            trace_list.append(go.Scatter(x=charging_rate.index, y=charging_rate, line_shape='hv', mode='markers+lines',
                                         name=f'{dataset_name} - CP Charging Rate', line=line_style))
        if 'grid_limit' in graph_toggle:
            trace_list.append(
                go.Scatter(x=df['time_of_day'].unique(), y=[GRID_LIMIT] * len(df['time_of_day'].unique()), mode='lines',
                           name='Grid Limit', line={'dash': 'dash'}))
        return trace_list

    def create_traces_total_energy(df, dataset_name):
        df_sorted = df.sort_values(by='time_of_day')
        total_energy = df_sorted.groupby('time_of_day')['cp_charge_increment'].sum().cumsum()
        return go.Scatter(x=total_energy.index, y=total_energy, line_shape='hv', mode='lines',
                          name=f'{dataset_name} - Cumulative Total Energy Used')

    def create_traces_cars_charging(df, dataset_name):
        cars_charging = df[df['cp_charging_rate'] > 0].groupby('time_of_day')['vehicle'].nunique()
        return go.Scatter(x=cars_charging.index, y=cars_charging, line_shape='hv', mode='lines',
                          name=f'{dataset_name} - Cars Currently Charging')

    graphs = []
    if view_toggle == 'combined':
        for dataset in data_toggle:
            df = data_map[dataset]
            name = 'Run 1' if dataset == 'df1' else 'Run 2'
            traces.extend(create_traces(df, name, {'dash': 'solid'}))

        layout = go.Layout(
            title={
                'text': 'Power Consumption',
                'font': {
                    'size': 24
                }
            },
            xaxis={'title': 'Time', 'tickformat': '%H:%M'},
            yaxis={'title': 'Power (kW)', 'tickformat': ',.0f'},
            barmode='group',
            plot_bgcolor='rgba(74, 74, 74, 1)',
            paper_bgcolor='rgba(44, 44, 44, 1)',
            font=dict(color='white'),
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
            hovermode='x unified'
        )
        if 'target_power' in graph_toggle or 'charging_rate' in graph_toggle:
            graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))

        if 'total_energy' in graph_toggle:
            for dataset in data_toggle:
                df = data_map[dataset]
                name = 'Run 1' if dataset == 'df1' else 'Run 2'
                total_energy_trace = create_traces_total_energy(df, name)
                total_energy_traces.append(total_energy_trace)

            energy_layout = go.Layout(
                title={
                    'text': 'Energy Used',
                    'font': {
                        'size': 24
                    }
                },
                xaxis={'title': 'Time', 'tickformat': '%H:%M'},
                yaxis={'title': 'Energy (kWh)', 'tickformat': ',.0f'},
                barmode='group',
                plot_bgcolor='rgba(74, 74, 74, 1)',
                paper_bgcolor='rgba(44, 44, 44, 1)',
                font=dict(color='white'),
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
                hovermode='x unified'
            )
            graphs.append(dcc.Graph(
                figure=go.Figure(data=total_energy_traces, layout=energy_layout)))

        if 'cars_charging' in graph_toggle:
            for dataset in data_toggle:
                df = data_map[dataset]
                name = 'Run 1' if dataset == 'df1' else 'Run 2'
                cars_charging_trace = create_traces_cars_charging(df, name)
                charging_cars_traces.append(cars_charging_trace)

            cars_layout = go.Layout(
                title={
                    'text': 'Number of EVs Charging',
                    'font': {
                        'size': 24
                    }
                },
                xaxis={'title': 'Time', 'tickformat': '%H:%M'},
                yaxis={'title': 'Number of EVs'},
                plot_bgcolor='rgba(74, 74, 74, 1)',
                paper_bgcolor='rgba(44, 44, 44, 1)',
                font=dict(color='white'),
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
                hovermode='x unified'
            )
            graphs.append(dcc.Graph(
                figure=go.Figure(data=charging_cars_traces, layout=cars_layout)))

    else:  # separate view
        for dataset in data_toggle:
            df = data_map[dataset]
            name = 'Run 1' if dataset == 'df1' else 'Run 2'
            traces = create_traces(df, name, {'dash': 'solid'})
            layout = go.Layout(
                title={
                    'text': f'Power Consumption in ({name})',
                    'font': {
                        'size': 24
                    }
                },
                xaxis={'title': 'Time', 'tickformat': '%H:%M'},
                yaxis={'title': 'Power (kW)', 'tickformat': ',.0f'},
                barmode='group',
                plot_bgcolor='rgba(74, 74, 74, 1)',
                paper_bgcolor='rgba(44, 44, 44, 1)',
                font=dict(color='white'),
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
                hovermode='x unified'
            )
            if 'target_power' in graph_toggle or 'charging_rate' in graph_toggle:
                graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))

        if 'total_energy' in graph_toggle:
            for dataset in data_toggle:
                df = data_map[dataset]
                name = 'Run 1' if dataset == 'df1' else 'Run 2'
                total_energy_trace = create_traces_total_energy(df, name)
                energy_layout = go.Layout(
                    title={
                        'text': f'Energy Used in {name}',
                        'font': {
                            'size': 24
                        }
                    },
                    xaxis={'title': 'Time', 'tickformat': '%H:%M'},
                    yaxis={'title': 'Energy (kWh)', 'tickformat': ',.0f'},
                    barmode='group',
                    plot_bgcolor='rgba(74, 74, 74, 1)',
                    paper_bgcolor='rgba(44, 44, 44, 1)',
                    font=dict(color='white'),
                    legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
                    hovermode='x unified'
                )
                graphs.append(dcc.Graph(
                    figure=go.Figure(data=[total_energy_trace], layout=energy_layout)))

        if 'cars_charging' in graph_toggle:
            for dataset in data_toggle:
                df = data_map[dataset]
                name = 'Run 1' if dataset == 'df1' else 'Run 2'
                cars_charging_trace = create_traces_cars_charging(df, name)
                cars_layout = go.Layout(
                    title={
                        'text': f'Number of EVs Charging in {name}',
                        'font': {
                            'size': 24
                        }
                    },
                    xaxis={'title': 'Time', 'tickformat': '%H:%M'},
                    yaxis={'title': 'Number of EVs'},
                    plot_bgcolor='rgba(74, 74, 74, 1)',
                    paper_bgcolor='rgba(44, 44, 44, 1)',
                    font=dict(color='white'),
                    legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
                    hovermode='x unified'
                )
                graphs.append(dcc.Graph(
                    figure=go.Figure(data=[cars_charging_trace], layout=cars_layout)))

    return graphs


@app.callback(
    Output('car-graph-container', 'children'),
    [Input('car-dropdown', 'value'),
     Input('view-toggle-cars', 'value'),
     Input('graph-toggle-cars', 'value')])

def update_car_graph(selected_car, view_toggle, graph_toggle):
    df1_filtered = df1[df1['vehicle'] == selected_car]
    df2_filtered = df2[df2['vehicle'] == selected_car]

    def create_traces(df, dataset_name, line_style):
        trace_list = []
        # if 'total_energy' in graph_toggle:
        #     df_sorted = df.sort_values(by='time_of_day')
        #     total_energy = df_sorted.groupby('time_of_day')['cp_charge_increment'].sum().cumsum()
        #     trace_list.append(go.Scatter(x=total_energy.index, y=total_energy, line_shape='hv', name=f'{dataset_name} - Cumulative Total Energy Used', mode='lines'))
        # if 'soc' in graph_toggle:
        #     soc = df.groupby('time_of_day')['vehicle_soc'].mean()
        #     trace_list.append(go.Scatter(x=soc.index, y=soc, mode='lines', line_shape='hv', name=f'{dataset_name} - State of Charge', line=line_style))
        if 'target_power' in graph_toggle:
            target_power = df.groupby('time_of_day')['cp_target_power'].mean()
            trace_list.append(go.Scatter(x=target_power.index, y=target_power, line_shape='hv', mode='lines', name=f'{dataset_name} - CP Target Power', line=line_style))
        if 'charging_rate' in graph_toggle:
            charging_rate = df.groupby('time_of_day')['cp_charging_rate'].mean()
            trace_list.append(go.Scatter(x=charging_rate.index, y=charging_rate, line_shape='hv', mode='lines', name=f'{dataset_name} - CP Charging Rate', line=line_style))
        return trace_list

    def create_traces_soc(df, dataset_name):
        trace_list = []
        soc = df.groupby('time_of_day')['vehicle_soc'].mean() * 100
        trace_list.append(go.Scatter(x=soc.index, y=soc, mode='lines', line_shape='hv', name=f'{dataset_name} - State of Charge'))
        return trace_list

    def create_traces_total_energy(df, dataset_name):
        trace_list = []
        df_sorted = df.sort_values(by='time_of_day')
        total_energy = df_sorted.groupby('time_of_day')['cp_charge_increment'].sum().cumsum()
        trace_list.append(go.Scatter(x=total_energy.index, y=total_energy, line_shape='hv', name=f'{dataset_name} - Cumulative Total Energy Used', mode='lines'))
        return trace_list

    graphs = []
    if view_toggle == 'combined':

        if 'target_power' in graph_toggle or 'charging_rate' in graph_toggle:
            traces = create_traces(df1_filtered, 'Run 1', {'dash': 'solid'}) + create_traces(df2_filtered, 'Run 2', {'dash': 'solid'})
            layout = go.Layout(
                title={
                    'text': f'Power Consumption EV{selected_car}',
                    'font': {
                        'size': 24
                    }
                },
                xaxis={'title': 'Time', 'tickformat': '%H:%M'},
                yaxis={'title': 'Power (kW)', 'tickformat': ',.0f'},
                barmode='group',
                plot_bgcolor='rgba(74, 74, 74, 1)',
                paper_bgcolor='rgba(44, 44, 44, 1)',
                font=dict(color='white'),
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
                hovermode='x unified'
            )
            graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))

        if 'soc' in graph_toggle:
            traces = create_traces_soc(df1_filtered, 'Run 1') + create_traces_soc(df2_filtered, 'Run 2')
            layout = go.Layout(
                title={
                    'text': f'State of Charge EV {selected_car}',
                    'font': {
                        'size': 24
                    }
                },
                xaxis={'title': 'Time', 'tickformat': '%H:%M'},
                yaxis={'title': 'State of Charge (%)', 'tickformat': ',.0f', 'range': [0, 100]},
                barmode='group',
                plot_bgcolor='rgba(74, 74, 74, 1)',
                paper_bgcolor='rgba(44, 44, 44, 1)',
                font=dict(color='white'),
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
                hovermode='x unified'
            )
            graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))

        if 'total_energy' in graph_toggle:
            traces = create_traces_total_energy(df1_filtered, 'Run 1') + create_traces_total_energy(df2_filtered, 'Run 2')

            energy_layout = go.Layout(
                title={
                    'text':f'Energy Used EV {selected_car}',
                    'font': {
                        'size': 24
                    }
                },
                xaxis={'title': 'Time', 'tickformat': '%H:%M'},
                yaxis={'title': 'Energy (kWh)', 'tickformat': ',.0f'},
                barmode='group',
                plot_bgcolor='rgba(74, 74, 74, 1)',
                paper_bgcolor='rgba(44, 44, 44, 1)',
                font=dict(color='white'),
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
                hovermode='x unified'
            )
            graphs.append(dcc.Graph(
                figure=go.Figure(data=traces, layout=energy_layout)))

    else:  # separate view

        if 'target_power' in graph_toggle or 'charging_rate' in graph_toggle:
            traces1 = create_traces(df1_filtered, 'Dataset 1', {'dash': 'solid'})
            traces2 = create_traces(df2_filtered, 'Dataset 2', {'dash': 'solid'})
            layout1 = go.Layout(
                title={
                    'text': f'Power Consumption EV {selected_car} (Run 1)',
                    'font': {
                        'size': 24
                    }
                },
                xaxis={'title': 'Time', 'tickformat': '%H:%M'},
                yaxis={'title': 'Power (kW)', 'tickformat': ',.0f'},
                barmode='group',
                plot_bgcolor='rgba(74, 74, 74, 1)',
                paper_bgcolor='rgba(44, 44, 44, 1)',
                font=dict(color='white'),
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
                hovermode='x unified'
            )
            layout2 = go.Layout(
                title={
                    'text': f'Power Consumption EV {selected_car} (Run 2)',
                    'font': {
                        'size': 24
                    }
                },
                xaxis={'title': 'Time', 'tickformat': '%H:%M'},
                yaxis={'title': 'Power (kW)', 'tickformat': ',.0f'},
                barmode='group',
                plot_bgcolor='rgba(74, 74, 74, 1)',
                paper_bgcolor='rgba(44, 44, 44, 1)',
                font=dict(color='white'),
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
                hovermode='x unified'
            )
            graphs.append(dcc.Graph(figure=go.Figure(data=traces1, layout=layout1)))
            graphs.append(dcc.Graph(figure=go.Figure(data=traces2, layout=layout2)))

        if 'soc' in graph_toggle:
            traces3 = create_traces_soc(df1_filtered, 'Run 1')
            traces4 = create_traces_soc(df2_filtered, 'Run 2')
            layout3 = go.Layout(
                title={
                    'text': f'State of Charge EV {selected_car} (Run 1)',
                    'font': {
                        'size': 24
                    }
                },
                xaxis={'title': 'Time', 'tickformat': '%H:%M'},
                yaxis={'title': 'State of Charge (%)', 'tickformat': ',.0f', 'range': [0, 100]},
                barmode='group',
                plot_bgcolor='rgba(74, 74, 74, 1)',
                paper_bgcolor='rgba(44, 44, 44, 1)',
                font=dict(color='white'),
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
                hovermode='x unified'
            )
            layout4 = go.Layout(
                title={
                    'text':f'State of Charge EV {selected_car} (Run 2)',
                    'font': {
                        'size': 24
                    }
                },
                xaxis={'title': 'Time', 'tickformat': '%H:%M'},
                yaxis={'title': 'State of Charge (%)', 'tickformat': ',.0f', 'range': [0, 100]},
                barmode='group',
                plot_bgcolor='rgba(74, 74, 74, 1)',
                paper_bgcolor='rgba(44, 44, 44, 1)',
                font=dict(color='white'),
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
                hovermode='x unified'
            )
            graphs.append(dcc.Graph(figure=go.Figure(data=traces3, layout=layout3)))
            graphs.append(dcc.Graph(figure=go.Figure(data=traces4, layout=layout4)))

        if 'total_energy' in graph_toggle:
            traces5 = create_traces_total_energy(df1_filtered, 'Run 1')
            traces6 = create_traces_total_energy(df2_filtered, 'Run 2')

            layout5 = go.Layout(
                title={
                    'text': f'Energy Used EV {selected_car} (Run 1)',
                    'font': {
                        'size': 24
                    }
                },
                xaxis={'title': 'Time', 'tickformat': '%H:%M'},
                yaxis={'title': 'Energy (kWh)', 'tickformat': ',.0f'},
                barmode='group',
                plot_bgcolor='rgba(74, 74, 74, 1)',
                paper_bgcolor='rgba(44, 44, 44, 1)',
                font=dict(color='white'),
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
                hovermode='x unified'
            )
            layout6 = go.Layout(
                title={
                    'text': f'Energy Used EV {selected_car} (Run 2)',
                    'font': {
                        'size': 24
                    }
                },
                xaxis={'title': 'Time', 'tickformat': '%H:%M'},
                yaxis={'title': 'Energy (kWh)', 'tickformat': ',.0f'},
                barmode='group',
                plot_bgcolor='rgba(74, 74, 74, 1)',
                paper_bgcolor='rgba(44, 44, 44, 1)',
                font=dict(color='white'),
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
                hovermode='x unified'
            )
            graphs.append(dcc.Graph(
                figure=go.Figure(data=traces5, layout=layout5)))
            graphs.append(dcc.Graph(
                figure=go.Figure(data=traces6, layout=layout6)))

    return graphs

@app.callback(
    Output('station-graph-container', 'children'),
    [Input('station-dropdown', 'value'),
     Input('view-toggle-stations', 'value'),
     Input('graph-toggle-stations', 'value')]
)
def update_station_graph(selected_station, view_toggle, graph_toggle):
    df1_filtered = df1[df1['cp'] == selected_station]
    df2_filtered = df2[df2['cp'] == selected_station]

    def create_traces(df, dataset_name, line_style):
        trace_list = []
        # if 'total_energy' in graph_toggle:
        #     df_sorted = df.sort_values(by='time_of_day')
        #     total_energy = df_sorted.groupby('time_of_day')['cp_charge_increment'].sum().cumsum()
        #     trace_list.append(go.Scatter(x=total_energy.index, y=total_energy, name=f'{dataset_name} - Cumulative Total Energy Used', mode='lines'))
        if 'target_power' in graph_toggle:
            target_power = df.groupby('time_of_day')['cp_target_power'].mean()
            trace_list.append(go.Scatter(x=target_power.index, y=target_power, mode='lines', line_shape='hv', name=f'{dataset_name} - CP Target Power', line=line_style))
        if 'charging_rate' in graph_toggle:
            charging_rate = df.groupby('time_of_day')['cp_charging_rate'].mean()
            trace_list.append(go.Scatter(x=charging_rate.index, y=charging_rate, mode='lines', line_shape='hv', name=f'{dataset_name} - CP Charging Rate', line=line_style))
        return trace_list

    graphs = []
    if view_toggle == 'combined':
        traces = create_traces(df1_filtered, 'Run 1', {'dash': 'solid'}) + create_traces(df2_filtered, 'Run 2', {'dash': 'solid'})
        layout = go.Layout(
            title={
                'text': f'Power Usage of Charging Station {selected_station}',
                'font': {
                    'size': 24
                }
            },
            xaxis={'title': 'Time', 'tickformat': '%H:%M'},
            yaxis={'title': 'Power (kW)', 'tickformat': ',.0f'},
            barmode='group',
            plot_bgcolor='rgba(74, 74, 74, 1)',
            paper_bgcolor='rgba(44, 44, 44, 1)',
            font=dict(color='white'),
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
            hovermode='x unified'
        )
        graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))
    else:  # separate view
        traces1 = create_traces(df1_filtered, 'Dataset 1', {'dash': 'solid'})
        traces2 = create_traces(df2_filtered, 'Dataset 2', {'dash': 'solid'})
        layout1 = go.Layout(
            title={
                'text': f'Power Usage of Charging Station {selected_station} (Run 1)',
                'font': {
                    'size': 24
                }
            },
            xaxis={'title': 'Time', 'tickformat': '%H:%M'},
            yaxis={'title': 'Power (kW)', 'tickformat': ',.0f'},
            barmode='group',
            plot_bgcolor='rgba(74, 74, 74, 1)',
            paper_bgcolor='rgba(44, 44, 44, 1)',
            font=dict(color='white'),
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
            hovermode='x unified'
        )
        layout2 = go.Layout(
            title={
                'text': f'Power Usage of Charging Station {selected_station} (Run 2)',
                'font': {
                    'size': 24
                }
            },
            xaxis={'title': 'Time', 'tickformat': '%H:%M'},
            yaxis={'title': 'Power (kW)', 'tickformat': ',.0f'},
            barmode='group',
            plot_bgcolor='rgba(74, 74, 74, 1)',
            paper_bgcolor='rgba(44, 44, 44, 1)',
            font=dict(color='white'),
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2),
            hovermode='x unified'
        )
        graphs.append(dcc.Graph(figure=go.Figure(data=traces1, layout=layout1)))
        graphs.append(dcc.Graph(figure=go.Figure(data=traces2, layout=layout2)))
    return graphs

if __name__ == '__main__':
    app.run_server(debug=True)