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
    df['vehicle'] = df['vehicle'].astype(str)
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
    total_energy_used = df['cp_charging_rate'].sum()
    cars_charged = df[df['vehicle_charge'] > 0]['vehicle'].nunique()
    cars_not_charged = df[df['vehicle_charge'] == 0]['vehicle'].nunique()

    # Filter cars that have the last 3 entries with cp_charge_increment, cp_charging_rate, and cp_target_power as zero
    last_3_entries = df.groupby('vehicle').tail(3)
    condition = (last_3_entries['cp_charge_increment'] == 0) & (last_3_entries['cp_charging_rate'] == 0) & (last_3_entries['cp_target_power'] == 0)
    vehicles_stopped_charging = last_3_entries[condition].groupby('vehicle').filter(lambda x: len(x) == 3)['vehicle'].unique()

    df_stopped_charging = df[df['vehicle'].isin(vehicles_stopped_charging)]
    avg_soc = df_stopped_charging.groupby('vehicle').tail(1)['vehicle_soc'].mean()
    median_soc = df_stopped_charging.groupby('vehicle').tail(1)['vehicle_soc'].median()

    return total_energy_used, cars_charged, cars_not_charged, avg_soc, median_soc

app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

#Base
app.layout = html.Div([
    html.Div([
        dcc.Link('Dashboard', href='/Dash', style={'padding': '10px'}),
        dcc.Link('Charging Infrastructure', href='/charging-infrastructure', style={'padding': '10px'}),
        dcc.Link('Cars', href='/cars', style={'padding': '10px'}),
        dcc.Link('Charging Station', href='/charging-station', style={'padding': '10px'}),
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
                value=['df1'],
                labelStyle={'display': 'block'}
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
                labelStyle={'display': 'block'}
            ),
            html.Hr(style={'border': '1px solid white', 'margin-top': '20px', 'margin-bottom': '20px'}),
            html.H3('Graph Options'),
            dcc.Checklist(
                id='graph-toggle-infrastructure',
                options=[
                    {'label': 'Total Energy Used', 'value': 'total_energy'},
                    {'label': 'CP Target Power', 'value': 'target_power'},
                    {'label': 'CP Charging Rate', 'value': 'charging_rate'},
                    {'label': 'Grid Limit', 'value': 'grid_limit'}
                ],
                value=['total_energy'],
                labelStyle={'display': 'block'}
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
                    value=df1['vehicle'].unique()[0]
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
                    labelStyle={'display': 'inline-block'}
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
                    value=['total_energy'],
                    labelStyle={'display': 'inline-block'}
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
                options=[{'label': station, 'value': station} for station in df1['cp'].unique()],
                value=df1['cp'].unique()[0]
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
                labelStyle={'display': 'inline-block'}
            ),
            html.Hr(style={'border': '1px solid white', 'margin-top': '20px', 'margin-bottom': '20px'}),
            html.H3('Graph Options'),
            dcc.Checklist(
                id='graph-toggle-stations',
                options=[
                    {'label': 'Total Energy Delivered', 'value': 'total_energy'},
                    {'label': 'Target Power over the Day', 'value': 'target_power'},
                    {'label': 'Charging Rate over the Day', 'value': 'charging_rate'}
                ],
                value=['total_energy'],
                labelStyle={'display': 'inline-block'}
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
    total_energy_1, cars_charged_1, cars_not_charged_1, avg_soc_1, median_soc_1 = calculate_kpis(df1)
    total_energy_2, cars_charged_2, cars_not_charged_2, avg_soc_2, median_soc_2 = calculate_kpis(df2)

    return dash_table.DataTable(
    data = [
        {'KPI': 'Total Energy Used (kWh)', 'Dataset 1': total_energy_1, 'Dataset 2': total_energy_2},
        {'KPI': 'Cars Charged', 'Dataset 1': cars_charged_1, 'Dataset 2': cars_charged_2},
        {'KPI': 'Cars Not Charged', 'Dataset 1': cars_not_charged_1, 'Dataset 2': cars_not_charged_2},
        {'KPI': 'Average SoC', 'Dataset 1': avg_soc_1, 'Dataset 2': avg_soc_2},
        {'KPI': 'Median SoC', 'Dataset 1': median_soc_1, 'Dataset 2': median_soc_2},
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
    style_as_list_view = True)

@app.callback(Output('infrastructure-graph-container', 'children'),
              [Input('data-toggle-infrastructure', 'value'),
               Input('view-toggle-infrastructure', 'value'),
               Input('graph-toggle-infrastructure', 'value')])
def update_infrastructure_graph(data_toggle, view_toggle, graph_toggle):
    data_map = {'df1': df1, 'df2': df2}
    traces = []

    def create_traces(df, dataset_name, line_style):
        trace_list = []
        if 'total_energy' in graph_toggle:
            df_sorted = df.sort_values(by='time_of_day')
            total_energy = df_sorted.groupby('time_of_day')['cp_charging_rate'].sum().cumsum()
            trace_list.append(go.Scatter(x=total_energy.index, y=total_energy, mode='lines', name=f'{dataset_name} - Cumulative Total Energy Used'))
        if 'target_power' in graph_toggle:
            target_power = df.groupby('time_of_day')['cp_target_power'].sum()
            trace_list.append(go.Scatter(x=target_power.index, y=target_power, mode='markers+lines', name=f'{dataset_name} - CP Target Power', line=line_style))
        if 'charging_rate' in graph_toggle:
            charging_rate = df.groupby('time_of_day')['cp_charging_rate'].sum()
            trace_list.append(go.Scatter(x=charging_rate.index, y=charging_rate, mode='markers+lines', name=f'{dataset_name} - CP Charging Rate', line=line_style))
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
            plot_bgcolor='rgba(74, 74, 74, 1)',
            paper_bgcolor='rgba(44, 44, 44, 1)',
            font=dict(color='white'),
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
                plot_bgcolor='rgba(74, 74, 74, 1)',
                paper_bgcolor='rgba(44, 44, 44, 1)',
                font=dict(color='white'),
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
            )
            graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))
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
            plot_bgcolor='rgba(74, 74, 74, 1)',
            paper_bgcolor='rgba(44, 44, 44, 1)',
            font=dict(color='white'),
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
            plot_bgcolor='rgba(74, 74, 74, 1)',
            paper_bgcolor='rgba(44, 44, 44, 1)',
            font=dict(color='white'),
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
        )
        layout2 = go.Layout(
            title=f'Car Data for {selected_car} (Dataset 2)',
            xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
            yaxis={'title': 'Value', 'tickformat': ',.0f'},
            barmode='group',
            plot_bgcolor='rgba(74, 74, 74, 1)',
            paper_bgcolor='rgba(44, 44, 44, 1)',
            font=dict(color='white'),
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
        )
        graphs.append(dcc.Graph(figure=go.Figure(data=traces1, layout=layout1)))
        graphs.append(dcc.Graph(figure=go.Figure(data=traces2, layout=layout2)))
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
            plot_bgcolor='rgba(74, 74, 74, 1)',
            paper_bgcolor='rgba(44, 44, 44, 1)',
            font=dict(color='white'),
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
            plot_bgcolor='rgba(74, 74, 74, 1)',
            paper_bgcolor='rgba(44, 44, 44, 1)',
            font=dict(color='white'),
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
        )
        layout2 = go.Layout(
            title=f'Charging Station Data for {selected_station} (Dataset 2)',
            xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
            yaxis={'title': 'Value', 'tickformat': ',.0f'},
            barmode='group',
            plot_bgcolor='rgba(74, 74, 74, 1)',
            paper_bgcolor='rgba(44, 44, 44, 1)',
            font=dict(color='white'),
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
        )
        graphs.append(dcc.Graph(figure=go.Figure(data=traces1, layout=layout1)))
        graphs.append(dcc.Graph(figure=go.Figure(data=traces2, layout=layout2)))
    return graphs

if __name__ == '__main__':
    app.run_server(debug=True)