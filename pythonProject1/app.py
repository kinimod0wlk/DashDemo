import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd

# Load data from CSV files
df1 = pd.read_csv('result1.csv', delimiter=';')
df2 = pd.read_csv('result2.csv', delimiter=';')

GRID_LIMIT = 1000

# Convert columns
def preprocess(df):
    df['time'] = df['time'].astype(int)
    df['vehicle'] = df['vehicle'].astype(str)
    df['cp_charging_rate'] = df['cp_charging_rate'].str.replace(',', '.').astype(float)
    df['cp_target_power'] = df['cp_target_power'].str.replace(',', '.').astype(float)
    df['vehicle_soc'] = df['vehicle_soc'].str.replace(',', '.').astype(float)
    df['vehicle_charge'] = df['vehicle_charge'].str.replace(',', '.').astype(float)
    df['vehicle_capacity'] = df['vehicle_capacity'].str.replace(',', '.').astype(float)
    df['cp_charge_increment'] = df['cp_charge_increment'].str.replace(',', '.').astype(float)
    df['time_minute'] = df['time'] / 60
    df['time_of_day'] = pd.to_datetime(df['time_minute'], unit='m', origin='2024-01-01').dt.strftime('%H:%M')
    return df

df1 = preprocess(df1)
df2 = preprocess(df2)

# Create the Dash app
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

# KPI functions
def calculate_kpis(df):
    total_energy_used = df['cp_charging_rate'].sum()
    cars_charged = df[df['vehicle_charge'] > 0]['vehicle'].nunique()
    cars_not_charged = df[df['vehicle_charge'] == 0]['vehicle'].nunique()
    return total_energy_used, cars_charged, cars_not_charged

# Dashboard Layout
dashboard_layout = html.Div([
    html.H1("Dashboard"),
    html.Div(id='kpis'),
])

# Charging Infrastructure Layout
charging_infrastructure_layout = html.Div([
    html.H1("Charging Infrastructure"),
    dcc.Checklist(
        id='data-toggle-infrastructure',
        options=[
            {'label': 'Dataset 1', 'value': 'df1'},
            {'label': 'Dataset 2', 'value': 'df2'}
        ],
        value=['df1'],
        labelStyle={'display': 'inline-block'}
    ),
    dcc.RadioItems(
        id='view-toggle-infrastructure',
        options=[
            {'label': 'Combined', 'value': 'combined'},
            {'label': 'Separate', 'value': 'separate'}
        ],
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

# Cars Layout
cars_layout = html.Div([
    html.H1("Cars"),
    dcc.Dropdown(
        id='car-dropdown',
        options=[{'label': car, 'value': car} for car in df1['vehicle'].unique()],
        value=df1['vehicle'].unique()[0]
    ),
    dcc.RadioItems(
        id='view-toggle-cars',
        options=[
            {'label': 'Combined', 'value': 'combined'},
            {'label': 'Separate', 'value': 'separate'}
        ],
        value='combined',
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Checklist(
        id='graph-toggle-cars',
        options=[
            {'label': 'Total Energy Used', 'value': 'total_energy'},
            {'label': 'State of Charge', 'value': 'soc'},
            {'label': 'CP Target Power', 'value': 'target_power'},
            {'label': 'CP Charging Rate', 'value': 'charging_rate'}
        ],
        value=['total_energy'],
        labelStyle={'display': 'inline-block'}
    ),
    html.Div(id='car-graph-container'),
])

# Charging Station Layout
charging_station_layout = html.Div([
    html.H1("Charging Station"),
    dcc.Dropdown(
        id='station-dropdown',
        options=[{'label': station, 'value': station} for station in df1['cp'].unique()],
        value=df1['cp'].unique()[0]
    ),
    dcc.RadioItems(
        id='view-toggle-stations',
        options=[
            {'label': 'Combined', 'value': 'combined'},
            {'label': 'Separate', 'value': 'separate'}
        ],
        value='combined',
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Checklist(
        id='graph-toggle-stations',
        options=[
            {'label': 'Total Energy Delivered', 'value': 'total_energy'},
            {'label': 'Target Power over the Day', 'value': 'target_power'},
            {'label': 'Charging Rate over the Day', 'value': 'charging_rate'}
        ],
        value=['total_energy'],
        labelStyle={'display': 'inline-block'}
    ),
    html.Div(id='station-graph-container'),
])

# Layout with location component and header
app.layout = html.Div([
    html.Div([
        dcc.Link('Dashboard', href='/'),
        dcc.Link('Charging Infrastructure', href='/charging-infrastructure'),
        dcc.Link('Cars', href='/cars'),
        dcc.Link('Charging Station', href='/charging-station'),
    ], style={'padding': '20px', 'backgroundColor': '#f0f0f0'}),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Callbacks for page navigation
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

# Callback to update KPIs on the dashboard
@app.callback(
    Output('kpis', 'children'),
    Input('url', 'pathname')
)
def update_kpis(pathname):
    if pathname == '/':
        total_energy_used_1, cars_charged_1, cars_not_charged_1 = calculate_kpis(df1)
        total_energy_used_2, cars_charged_2, cars_not_charged_2 = calculate_kpis(df2)
        return html.Div([
            html.H2("Dataset 1 KPIs"),
            html.P(f"Total Energy Used in Simulation: {total_energy_used_1} kWh"),
            html.P(f"Amount of Cars charged: {cars_charged_1}"),
            html.P(f"Amount of Cars not charged: {cars_not_charged_1}"),
            html.H2("Dataset 2 KPIs"),
            html.P(f"Total Energy Used in Simulation: {total_energy_used_2} kWh"),
            html.P(f"Amount of Cars charged: {cars_charged_2}"),
            html.P(f"Amount of Cars not charged: {cars_not_charged_2}"),
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
            barmode='group',
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
        )
        graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))
    else:  # separate view
        for dataset in data_toggle:
            df = data_map[dataset]
            traces = create_traces(df, dataset, {'dash': 'solid'})
            layout = go.Layout(
                title=f'Charging Infrastructure Data ({dataset})',
                xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
                yaxis={'title': 'Value', 'tickformat': ',.0f'},
                barmode='group',
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
            )
            graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))
    return graphs

# Callback to update the graph in the Cars tab
@app.callback(
    Output('car-graph-container', 'children'),
    [Input('car-dropdown', 'value'),
     Input('view-toggle-cars', 'value'),
     Input('graph-toggle-cars', 'value')]
)
def update_car_graph(selected_car, view_toggle, graph_toggle):
    df1_filtered = df1[df1['vehicle'] == selected_car]
    df2_filtered = df2[df2['vehicle'] == selected_car]

    def create_traces(df, dataset_name, line_style):
        trace_list = []
        if 'total_energy' in graph_toggle:
            df_sorted = df.sort_values(by='time_of_day')
            total_energy = df_sorted.groupby('time_of_day')['cp_charging_rate'].sum().cumsum()
            trace_list.append(go.Bar(x=total_energy.index, y=total_energy, name=f'{dataset_name} - Cumulative Total Energy Used'))
        if 'soc' in graph_toggle:
            soc = df.groupby('time_of_day')['vehicle_soc'].mean()
            trace_list.append(go.Scatter(x=soc.index, y=soc, mode='lines', name=f'{dataset_name} - State of Charge', line=line_style))
        if 'target_power' in graph_toggle:
            target_power = df.groupby('time_of_day')['cp_target_power'].mean()
            trace_list.append(go.Scatter(x=target_power.index, y=target_power, mode='lines', name=f'{dataset_name} - CP Target Power', line=line_style))
        if 'charging_rate' in graph_toggle:
            charging_rate = df.groupby('time_of_day')['cp_charging_rate'].mean()
            trace_list.append(go.Scatter(x=charging_rate.index, y=charging_rate, mode='lines', name=f'{dataset_name} - CP Charging Rate', line=line_style))
        return trace_list

    graphs = []
    if view_toggle == 'combined':
        traces = create_traces(df1_filtered, 'Dataset 1', {'dash': 'solid'}) + create_traces(df2_filtered, 'Dataset 2', {'dash': 'solid'})
        layout = go.Layout(
            title=f'Car Data for {selected_car}',
            xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
            yaxis={'title': 'Value', 'tickformat': ',.0f'},
            barmode='group',
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
        )
        graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))
    else:  # separate view
        traces1 = create_traces(df1_filtered, 'Dataset 1', {'dash': 'solid'})
        traces2 = create_traces(df2_filtered, 'Dataset 2', {'dash': 'dot'})
        layout1 = go.Layout(
            title=f'Car Data for {selected_car} (Dataset 1)',
            xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
            yaxis={'title': 'Value', 'tickformat': ',.0f'},
            barmode='group',
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
        )
        layout2 = go.Layout(
            title=f'Car Data for {selected_car} (Dataset 2)',
            xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
            yaxis={'title': 'Value', 'tickformat': ',.0f'},
            barmode='group',
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
        )
        graphs.append(dcc.Graph(figure=go.Figure(data=traces1, layout=layout1)))
        graphs.append(dcc.Graph(figure=go.Figure(data=traces2, layout=layout2)))
    return graphs

# Callback to update the graph in the Charging Station tab
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
        return trace_list

    graphs = []
    if view_toggle == 'combined':
        traces = create_traces(df1_filtered, 'Dataset 1', {'dash': 'solid'}) + create_traces(df2_filtered, 'Dataset 2', {'dash': 'solid'})
        layout = go.Layout(
            title=f'Charging Station Data for {selected_station}',
            xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
            yaxis={'title': 'Value', 'tickformat': ',.0f'},
            barmode='group',
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
        )
        graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))
    else:  # separate view
        traces1 = create_traces(df1_filtered, 'Dataset 1', {'dash': 'solid'})
        traces2 = create_traces(df2_filtered, 'Dataset 2', {'dash': 'dot'})
        layout1 = go.Layout(
            title=f'Charging Station Data for {selected_station} (Dataset 1)',
            xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
            yaxis={'title': 'Value', 'tickformat': ',.0f'},
            barmode='group',
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
        )
        layout2 = go.Layout(
            title=f'Charging Station Data for {selected_station} (Dataset 2)',
            xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
            yaxis={'title': 'Value', 'tickformat': ',.0f'},
            barmode='group',
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
        )
        graphs.append(dcc.Graph(figure=go.Figure(data=traces1, layout=layout1)))
        graphs.append(dcc.Graph(figure=go.Figure(data=traces2, layout=layout2)))
    return graphs

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
