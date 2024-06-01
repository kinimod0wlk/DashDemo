import dash
from dash import dcc, dash_table, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd

# Load data from CSV files
df1 = pd.read_csv('result1.csv', delimiter=';')
df2 = pd.read_csv('result2.csv', delimiter=';')

# Convert columns to appropriate types
def preprocess(df):
    df['time'] = df['time'].astype(int)
    df['vehicle'] = df['vehicle'].astype(str)
    df['cp_charging_rate'] = df['cp_charging_rate'].str.replace(',', '.').astype(float)
    df['cp_target_power'] = df['cp_target_power'].str.replace(',', '.').astype(float)
    df['vehicle_soc'] = df['vehicle_soc'].str.replace(',', '.').astype(float)
    df['vehicle_charge'] = df['vehicle_charge'].str.replace(',', '.').astype(float)
    df['vehicle_capacity'] = df['vehicle_capacity'].str.replace(',', '.').astype(float)
    df['cp_charge_increment'] = df['cp_charge_increment'].str.replace(',', '.').astype(float)
    df['time_minute'] = df['time'] // 60
    df['time_of_day'] = pd.to_datetime(df['time'], unit='m', origin='2024-01-01').dt.strftime('%H:%M')
    return df

df1 = preprocess(df1)
df2 = preprocess(df2)

# Create the Dash app
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

# Define functions to create figures
def get_ev_consumption(df, name):
    ev_consumption = df.groupby(['time_minute', 'vehicle'])['cp_charging_rate'].sum().unstack().fillna(0)
    return [go.Scatter(x=ev_consumption.index, y=ev_consumption[vehicle], mode='lines', name=f'{name} EV {vehicle}') for vehicle in ev_consumption.columns]

def get_total_energy_usage(df, name):
    df['building_usage'] = 10  # Replace with actual building usage data if available
    total_energy_usage = df.groupby('time_minute')['cp_charging_rate'].sum() + df.groupby('time_minute')['building_usage'].mean()
    return go.Scatter(x=total_energy_usage.index, y=total_energy_usage, mode='lines', name=f'{name} Total Energy Usage')

def get_utilization_of_own_cps(df, name):
    own_cp_usage = df[df['cp'].astype(str).str.contains('own')]
    shared_cp_usage = df[~df['cp'].astype(str).str.contains('own')]
    own_usage_trace = go.Scatter(x=own_cp_usage['time_minute'], y=own_cp_usage['cp_charging_rate'], mode='lines', name=f'{name} Own CP Usage')
    shared_usage_trace = go.Scatter(x=shared_cp_usage['time_minute'], y=shared_cp_usage['cp_charging_rate'], mode='lines', name=f'{name} Shared CP Usage')
    return [own_usage_trace, shared_usage_trace]

def get_charged_kwh_per_ev(df, name):
    charged_kwh = df.groupby('vehicle')['cp_charge_increment'].sum()
    return go.Bar(x=charged_kwh.index, y=charged_kwh, name=f'{name} Charged kWh per EV')

def get_ev_times(df, name):
    arrival_time = df[df['type'] == 'A']
    waiting_time = df[df['type'] == 'W']
    charging_time = df[df['type'] == 'C']
    parking_time = df[df['type'] == 'P']
    arrival_trace = go.Scatter(x=arrival_time['time_minute'], y=arrival_time['vehicle'], mode='markers', name=f'{name} Arrival Time')
    waiting_trace = go.Scatter(x=waiting_time['time_minute'], y=waiting_time['vehicle'], mode='markers', name=f'{name} Waiting Time')
    charging_trace = go.Scatter(x=charging_time['time_minute'], y=charging_time['vehicle'], mode='markers', name=f'{name} Charging Time')
    parking_trace = go.Scatter(x=parking_time['time_minute'], y=parking_time['vehicle'], mode='markers', name=f'{name} Parking Time')
    return [arrival_trace, waiting_trace, charging_trace, parking_trace]

def get_vehicle_charge_over_time(df, name):
    vehicle_charge = df.groupby(['time_minute', 'vehicle'])['vehicle_charge'].mean().unstack().fillna(0)
    return [go.Scatter(x=vehicle_charge.index, y=vehicle_charge[vehicle], mode='lines', name=f'{name} EV {vehicle} Charge') for vehicle in vehicle_charge.columns]

def create_figure(traces, title, xaxis_title, yaxis_title):
    return go.Figure(data=traces, layout=go.Layout(title=title, xaxis={'title': xaxis_title}, yaxis={'title': yaxis_title}))

# Define page layouts
layout_ev_consumption = html.Div([
    html.H1("EV Consumption per Minute"),
    dcc.Checklist(
        id='data-toggle-ev-consumption',
        options=[
            {'label': 'Dataset 1', 'value': 'df1'},
            {'label': 'Dataset 2', 'value': 'df2'}
        ],
        value=['df1'],
        labelStyle={'display': 'inline-block'}
    ),
    dcc.RadioItems(
        id='view-toggle-ev-consumption',
        options=[
            {'label': 'Combined', 'value': 'combined'},
            {'label': 'Separate', 'value': 'separate'}
        ],
        value='combined',
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Graph(id='ev-consumption-per-minute'),
    html.Div(id='second-ev-consumption-graph'),
    html.Div([
        dcc.Link('Next Page', href='/total-energy-usage'),
    ])
])

layout_total_energy = html.Div([
    html.H1("Total Energy Usage per Minute"),
    dcc.Checklist(
        id='data-toggle-total-energy',
        options=[
            {'label': 'Dataset 1', 'value': 'df1'},
            {'label': 'Dataset 2', 'value': 'df2'}
        ],
        value=['df1'],
        labelStyle={'display': 'inline-block'}
    ),
    dcc.RadioItems(
        id='view-toggle-total-energy',
        options=[
            {'label': 'Combined', 'value': 'combined'},
            {'label': 'Separate', 'value': 'separate'}
        ],
        value='combined',
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Graph(id='total-energy-usage-per-minute'),
    html.Div(id='second-total-energy-graph'),
    html.Div([
        dcc.Link('Previous Page', href='/ev-consumption'),
        dcc.Link('Next Page', href='/utilization-of-own-cps'),
    ])
])

layout_utilization = html.Div([
    html.H1("Utilization of Own CPs"),
    dcc.Checklist(
        id='data-toggle-utilization',
        options=[
            {'label': 'Dataset 1', 'value': 'df1'},
            {'label': 'Dataset 2', 'value': 'df2'}
        ],
        value=['df1'],
        labelStyle={'display': 'inline-block'}
    ),
    dcc.RadioItems(
        id='view-toggle-utilization',
        options=[
            {'label': 'Combined', 'value': 'combined'},
            {'label': 'Separate', 'value': 'separate'}
        ],
        value='combined',
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Graph(id='utilization-of-own-cps'),
    html.Div(id='second-utilization-graph'),
    html.Div([
        dcc.Link('Previous Page', href='/total-energy-usage'),
        dcc.Link('Next Page', href='/charged-kwh-per-ev'),
    ])
])

layout_charged_kwh = html.Div([
    html.H1("Charged kWh per EV"),
    dcc.Checklist(
        id='data-toggle-charged-kwh',
        options=[
            {'label': 'Dataset 1', 'value': 'df1'},
            {'label': 'Dataset 2', 'value': 'df2'}
        ],
        value=['df1'],
        labelStyle={'display': 'inline-block'}
    ),
    dcc.RadioItems(
        id='view-toggle-charged-kwh',
        options=[
            {'label': 'Combined', 'value': 'combined'},
            {'label': 'Separate', 'value': 'separate'}
        ],
        value='combined',
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Graph(id='charged-kwh-per-ev'),
    html.Div(id='second-charged-kwh-graph'),
    html.Div([
        dcc.Link('Previous Page', href='/utilization-of-own-cps'),
        dcc.Link('Next Page', href='/ev-times'),
    ])
])

layout_ev_times = html.Div([
    html.H1("EV Times"),
    dcc.Checklist(
        id='data-toggle-ev-times',
        options=[
            {'label': 'Dataset 1', 'value': 'df1'},
            {'label': 'Dataset 2', 'value': 'df2'}
        ],
        value=['df1'],
        labelStyle={'display': 'inline-block'}
    ),
    dcc.RadioItems(
        id='view-toggle-ev-times',
        options=[
            {'label': 'Combined', 'value': 'combined'},
            {'label': 'Separate', 'value': 'separate'}
        ],
        value='combined',
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Graph(id='ev-times'),
    html.Div(id='second-ev-times-graph'),
    html.Div([
        dcc.Link('Previous Page', href='/charged-kwh-per-ev'),
        dcc.Link('Next Page', href='/vehicle-charge'),
    ])
])

layout_vehicle_charge = html.Div([
    html.H1("Vehicle Charge Over Time"),
    dcc.Checklist(
        id='data-toggle-vehicle-charge',
        options=[
            {'label': 'Dataset 1', 'value': 'df1'},
            {'label': 'Dataset 2', 'value': 'df2'}
        ],
        value=['df1'],
        labelStyle={'display': 'inline-block'}
    ),
    dcc.RadioItems(
        id='view-toggle-vehicle-charge',
        options=[
            {'label': 'Combined', 'value': 'combined'},
            {'label': 'Separate', 'value': 'separate'}
        ],
        value='combined',
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Graph(id='vehicle-charge-over-time'),
    html.Div(id='second-vehicle-charge-graph'),
    html.Div([
        dcc.Link('Previous Page', href='/ev-times'),
    ])
])

# Define the layout with a location component
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Define the callbacks for page navigation
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/total-energy-usage':
        return layout_total_energy
    elif pathname == '/utilization-of-own-cps':
        return layout_utilization
    elif pathname == '/charged-kwh-per-ev':
        return layout_charged_kwh
    elif pathname == '/ev-times':
        return layout_ev_times
    elif pathname == '/vehicle-charge':
        return layout_vehicle_charge
    else:
        return layout_ev_consumption

# Define callbacks to update graphs
@app.callback(
    [Output('ev-consumption-per-minute', 'figure'),
     Output('second-ev-consumption-graph', 'children')],
    [Input('data-toggle-ev-consumption', 'value'),
     Input('view-toggle-ev-consumption', 'value')]
)
def update_ev_consumption(datasets, view):
    data_map = {'df1': df1, 'df2': df2}
    traces = []
    if view == 'combined':
        for dataset in datasets:
            traces.extend(get_ev_consumption(data_map[dataset], dataset))
        return create_figure(traces, 'EV Consumption per Minute', 'Time (minutes)', 'kW Usage'), None
    else:
        figures = []
        for dataset in datasets:
            traces = get_ev_consumption(data_map[dataset], dataset)
            figures.append(dcc.Graph(figure=create_figure(traces, f'{dataset} EV Consumption per Minute', 'Time (minutes)', 'kW Usage')))
        return create_figure([], 'EV Consumption per Minute', 'Time (minutes)', 'kW Usage'), html.Div(figures)

@app.callback(
    [Output('total-energy-usage-per-minute', 'figure'),
     Output('second-total-energy-graph', 'children')],
    [Input('data-toggle-total-energy', 'value'),
     Input('view-toggle-total-energy', 'value')]
)
def update_total_energy_usage(datasets, view):
    data_map = {'df1': df1, 'df2': df2}
    traces = []
    if view == 'combined':
        for dataset in datasets:
            traces.append(get_total_energy_usage(data_map[dataset], dataset))
        return create_figure(traces, 'Total Energy Usage per Minute', 'Time (minutes)', 'Total kW Usage'), None
    else:
        figures = []
        for dataset in datasets:
            traces = [get_total_energy_usage(data_map[dataset], dataset)]
            figures.append(dcc.Graph(figure=create_figure(traces, f'{dataset} Total Energy Usage per Minute', 'Time (minutes)', 'Total kW Usage')))
        return create_figure([], 'Total Energy Usage per Minute', 'Time (minutes)', 'Total kW Usage'), html.Div(figures)

@app.callback(
    [Output('utilization-of-own-cps', 'figure'),
     Output('second-utilization-graph', 'children')],
    [Input('data-toggle-utilization', 'value'),
     Input('view-toggle-utilization', 'value')]
)
def update_utilization(datasets, view):
    data_map = {'df1': df1, 'df2': df2}
    traces = []
    if view == 'combined':
        for dataset in datasets:
            traces.extend(get_utilization_of_own_cps(data_map[dataset], dataset))
        return create_figure(traces, 'Utilization of Own CPs', 'Time (minutes)', 'kW Usage'), None
    else:
        figures = []
        for dataset in datasets:
            traces = get_utilization_of_own_cps(data_map[dataset], dataset)
            figures.append(dcc.Graph(figure=create_figure(traces, f'{dataset} Utilization of Own CPs', 'Time (minutes)', 'kW Usage')))
        return create_figure([], 'Utilization of Own CPs', 'Time (minutes)', 'kW Usage'), html.Div(figures)

@app.callback(
    [Output('charged-kwh-per-ev', 'figure'),
     Output('second-charged-kwh-graph', 'children')],
    [Input('data-toggle-charged-kwh', 'value'),
     Input('view-toggle-charged-kwh', 'value')]
)
def update_charged_kwh(datasets, view):
    data_map = {'df1': df1, 'df2': df2}
    traces = []
    if view == 'combined':
        for dataset in datasets:
            traces.append(get_charged_kwh_per_ev(data_map[dataset], dataset))
        return create_figure(traces, 'Charged kWh per EV', 'Vehicle', 'kWh Charged'), None
    else:
        figures = []
        for dataset in datasets:
            traces = [get_charged_kwh_per_ev(data_map[dataset], dataset)]
            figures.append(dcc.Graph(figure=create_figure(traces, f'{dataset} Charged kWh per EV', 'Vehicle', 'kWh Charged')))
        return create_figure([], 'Charged kWh per EV', 'Vehicle', 'kWh Charged'), html.Div(figures)

@app.callback(
    [Output('ev-times', 'figure'),
     Output('second-ev-times-graph', 'children')],
    [Input('data-toggle-ev-times', 'value'),
     Input('view-toggle-ev-times', 'value')]
)
def update_ev_times(datasets, view):
    data_map = {'df1': df1, 'df2': df2}
    traces = []
    if view == 'combined':
        for dataset in datasets:
            traces.extend(get_ev_times(data_map[dataset], dataset))
        return create_figure(traces, 'EV Times', 'Time (minutes)', 'Vehicle'), None
    else:
        figures = []
        for dataset in datasets:
            traces = get_ev_times(data_map[dataset], dataset)
            figures.append(dcc.Graph(figure=create_figure(traces, f'{dataset} EV Times', 'Time (minutes)', 'Vehicle')))
        return create_figure([], 'EV Times', 'Time (minutes)', 'Vehicle'), html.Div(figures)

@app.callback(
    [Output('vehicle-charge-over-time', 'figure'),
     Output('second-vehicle-charge-graph', 'children')],
    [Input('data-toggle-vehicle-charge', 'value'),
     Input('view-toggle-vehicle-charge', 'value')]
)
def update_vehicle_charge(datasets, view):
    data_map = {'df1': df1, 'df2': df2}
    traces = []
    if view == 'combined':
        for dataset in datasets:
            traces.extend(get_vehicle_charge_over_time(data_map[dataset], dataset))
        return create_figure(traces, 'Vehicle Charge Over Time', 'Time (minutes)', 'Charge (kWh)'), None
    else:
        figures = []
        for dataset in datasets:
            traces = get_vehicle_charge_over_time(data_map[dataset], dataset)
            figures.append(dcc.Graph(figure=create_figure(traces, f'{dataset} Vehicle Charge Over Time', 'Time (minutes)', 'Charge (kWh)')))
        return create_figure([], 'Vehicle Charge Over Time', 'Time (minutes)', 'Charge (kWh)'), html.Div(figures)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)