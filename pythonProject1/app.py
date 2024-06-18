import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd

# Load the CSV files
df1 = pd.read_csv('result1.csv', delimiter=';')
df2 = pd.read_csv('result2.csv', delimiter=';')

# Set the grid limit constant
GRID_LIMIT = 1000

# Function to preprocess the dataframes
def preprocess(df):
    df['time'] = df['time'].astype(int)
    df['vehicle'] = df['vehicle'].astype(str)
    df['vehicle_soc'] = df['vehicle_soc'].str.replace(',', '.').astype(float)
    df['vehicle_charge'] = df['vehicle_charge'].str.replace(',', '.').astype(float)
    df['vehicle_capacity'] = df['vehicle_capacity'].str.replace(',', '.').astype(float)
    df['cp_charge_increment'] = df['cp_charge_increment'].str.replace(',', '.').astype(float)
    df['time_minute'] = df['time'] / 60
    df['time_of_day'] = pd.to_datetime(df['time_minute'], unit='m', origin='2024-01-01').dt.strftime('%H:%M')
    return df

df1 = preprocess(df1)
df2 = preprocess(df2)

# Initialize the Dash app
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

# Function to calculate KPIs
def calculate_kpis(df):
    total_energy_used = df['cp_charging_rate'].sum()
    cars_charged = df[df['vehicle_charge'] > 0]['vehicle'].nunique()
    cars_not_charged = df[df['vehicle_charge'] == 0]['vehicle'].nunique()
    return total_energy_used, cars_charged, cars_not_charged

# Define the layout for the dashboard
dashboard_layout = html.Div([
    html.H1("Dashboard"),
    html.Div(id='kpis'),
])

# Define the layout for the Charging Infrastructure tab
charging_infrastructure_layout = html.Div([
    dcc.Checklist(
        id='data-toggle-infrastructure',
        options=[{'label': 'Dataset 1', 'value': 'df1'}, {'label': 'Dataset 2', 'value': 'df2'}],
        value=['df1'],
        labelStyle={'display': 'inline-block'}
    ),
    dcc.RadioItems(
        id='view-toggle-infrastructure',
        options=[{'label': 'Combined View', 'value': 'combined'}, {'label': 'Separate View', 'value': 'separate'}],
        value='combined',
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Checklist(
        id='graph-toggle-infrastructure',
        options=[
            {'label': 'Total Energy Used', 'value': 'total_energy'},
            {'label': 'CP Target Power', 'value': 'target_power'},
            {'label': 'CP Charging Rate', 'value': 'charging_rate'},
            {'label': 'Grid Limit', 'value': 'grid_limit'}
        ],
        value=['total_energy'],
        labelStyle={'display': 'inline-block'}
    ),
    html.Div(id='infrastructure-graph-container'),
])

# Define the layout for the Cars tab
cars_layout = html.Div([
    dcc.Dropdown(
        id='car-dropdown',
        options=[{'label': car, 'value': car} for car in df1['vehicle'].unique()],
        value=df1['vehicle'].unique()[0]
    ),
    dcc.RadioItems(
        id='view-toggle-cars',
        options=[{'label': 'Combined View', 'value': 'combined'}, {'label': 'Separate View', 'value': 'separate'}],
        value='combined',
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Checklist(
        id='graph-toggle-cars',
        options=[
            {'label': 'Total Energy Used', 'value': 'total_energy'},
            {'label': 'State of Charge (SoC)', 'value': 'soc'},
            {'label': 'CP Target Power', 'value': 'target_power'},
            {'label': 'CP Charging Rate', 'value': 'charging_rate'}
        ],
        value=['total_energy'],
        labelStyle={'display': 'inline-block'}
    ),
    html.Div(id='car-graph-container'),
])

# Define the layout for the Charging Station tab
charging_station_layout = html.Div([
    dcc.Dropdown(
        id='station-dropdown',
        options=[{'label': station, 'value': station} for station in df1['cp'].unique()],
        value=df1['cp'].unique()[0]
    ),
    dcc.RadioItems(
        id='view-toggle-stations',
        options=[{'label': 'Combined View', 'value': 'combined'}, {'label': 'Separate View', 'value': 'separate'}],
        value='combined',
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Checklist(
        id='graph-toggle-stations',
        options=[
            {'label': 'Total Energy Used', 'value': 'total_energy'},
            {'label': 'CP Target Power', 'value': 'target_power'},
            {'label': 'CP Charging Rate', 'value': 'charging_rate'}
        ],
        value=['total_energy'],
        labelStyle={'display': 'inline-block'}
    ),
    html.Div(id='station-graph-container'),
])

# Main layout with a location component and header
app.layout = html.Div([
    html.Div([
        dcc.Link('Dashboard', href='/'),
        dcc.Link('Charging Infrastructure', href='/charging-infrastructure'),
        dcc.Link('Cars', href='/cars'),
        dcc.Link('Charging Station', href='/charging-station'),
    ]),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Callback for page navigation
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/charging-infrastructure':
        return charging_infrastructure_layout
    elif pathname == '/cars':
        return cars_layout
    elif pathname == '/charging-station':
        return charging_station_layout
    else:
        return dashboard_layout

# Callback to update the KPIs on the dashboard
@app.callback(Output('kpis', 'children'),
              Input('url', 'pathname'))
def update_kpis(pathname):
    total_energy_1, cars_charged_1, cars_not_charged_1 = calculate_kpis(df1)
    total_energy_2, cars_charged_2, cars_not_charged_2 = calculate_kpis(df2)
    return html.Div([
        html.P(f"Dataset 1 - Total Energy Used: {total_energy_1} kWh"),
        html.P(f"Dataset 1 - Amount of Cars Charged: {cars_charged_1}"),
        html.P(f"Dataset 1 - Amount of Cars not charged: {cars_not_charged_1}"),
        html.P(f"Dataset 2 - Total Energy Used: {total_energy_2} kWh"),
        html.P(f"Dataset 2 - Amount of Cars Charged: {cars_charged_2}"),
        html.P(f"Dataset 2 - Amount of Cars not charged: {cars_not_charged_2}"),
    ])

# Callback to update the graph in the Charging Infrastructure tab
@app.callback(
    Output('infrastructure-graph-container', 'children'),
    [Input('data-toggle-infrastructure', 'value'),
     Input('view-toggle-infrastructure', 'value'),
     Input('graph-toggle-infrastructure', 'value')]
)
def update_infrastructure_graph(data_toggle, view_toggle, graph_toggle):
    data_map = {'df1': df1, 'df2': df2}
    traces = []

    def create_traces(df, dataset_name, line_style):
        trace_list = []
        if 'total_energy' in graph_toggle:
            df_sorted = df.sort_values(by='time_of_day')
            total_energy = df_sorted.groupby('time_of_day')['cp_charging_rate'].sum().cumsum()
            trace_list.append(go.Bar(x=total_energy.index, y=total_energy, name=f'{dataset_name} - Cumulative Total Energy Used'))
        if 'target_power' in graph_toggle:
            target_power = df.groupby('time_of_day')['cp_target_power'].mean()
            trace_list.append(go.Scatter(x=target_power.index, y=target_power, mode='lines', name=f'{dataset_name} - CP Target Power', line=line_style))
        if 'charging_rate' in graph_toggle:
            charging_rate = df.groupby('time_of_day')['cp_charging_rate'].mean()
            trace_list.append(go.Scatter(x=charging_rate.index, y=charging_rate, mode='lines', name=f'{dataset_name} - CP Charging Rate', line=line_style))
        if 'grid_limit' in graph_toggle:
            trace_list.append(go.Scatter(x=df['time_of_day'].unique(), y=[GRID_LIMIT]*len(df['time_of_day'].unique()), mode='lines', name='Grid Limit', line={'dash': 'dash'}))
        return trace_list

    graphs = []
    if view_toggle == 'combined':
        for dataset in data_toggle:
            df = data_map[dataset]
            traces.extend(create_traces(df, dataset, {'dash': 'solid'}))
        layout = go.Layout(
            title='Charging Infrastructure Data',
            xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
            yaxis={'title': 'Value', 'tickformat': ',.0f'},
            barmode='group'
        )
        graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))
    elif view_toggle == 'separate':
        for dataset in data_toggle:
            df = data_map[dataset]
            traces = create_traces(df, dataset, {'dash': 'solid'})
            layout = go.Layout(
                title=f'{dataset} - Charging Infrastructure Data',
                xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
                yaxis={'title': 'Value', 'tickformat': ',.0f'},
                barmode='group'
            )
            graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))
    return html.Div(graphs)

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
