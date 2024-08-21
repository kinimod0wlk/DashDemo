import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd

# Load data from CSV files
df1 = pd.read_csv('result1.csv', delimiter=';')
df2 = pd.read_csv('result2.csv', delimiter=';')

for car in df1["vehicle"].unique():
    if car in df2["vehicle"].unique():

        for key in df1[df1["vehicle"] == car]["time"].unique():
            if not ((df2["vehicle"] == car) & (df2["time"] == key)).any():
                new_row = {"time": key, "vehicle": car}
                df2 = pd.concat([df2, pd.DataFrame([new_row])], ignore_index=True)


for car in df2["vehicle"].unique():
    if car in df1["vehicle"].unique():
        for key in df2[df2["vehicle"] == car]["time"].unique():
            if not ((df1["vehicle"] == car) & (df1["time"] == key)).any():
                new_row = {"time": key, "vehicle": car}
                df1 = pd.concat([df1, pd.DataFrame([new_row])], ignore_index=True)

merged_df = pd.merge(df1, df2,
                     on=["vehicle", "time"],
                     how="outer",
                     suffixes=('_df1', '_df2'))

#merged_df.to_csv('result_D.csv', index=False, sep=';')

def preprocess(df):

    # CSV 1
    df['time'] = df['time'].astype(int)
    df['vehicle'] = df['vehicle'].astype(str)
    df['vehicle_soc_df1'] = df['vehicle_soc_df1'].str.replace(',', '.').astype(float)
    df['vehicle_charge_df1'] = df['vehicle_charge_df1'].str.replace(',', '.').astype(float)
    df['vehicle_capacity_df1'] = df['vehicle_capacity_df1'].str.replace(',', '.').astype(float)
    df['cp_charge_increment_df1'] = df['cp_charge_increment_df1'].str.replace(',', '.').astype(float)
    df['cp_charging_rate_df1'] = df['cp_charging_rate_df1'].str.replace(',', '.').astype(float)
    df['cp_target_power_df1'] = df['cp_target_power_df1'].str.replace(',', '.').astype(float)

    # CSV 2
    df['vehicle_soc_df2'] = df['vehicle_soc_df2'].str.replace(',', '.').astype(float)
    df['vehicle_charge_df2'] = df['vehicle_charge_df2'].str.replace(',', '.').astype(float)
    df['vehicle_capacity_df2'] = df['vehicle_capacity_df2'].str.replace(',', '.').astype(float)
    df['cp_charge_increment_df2'] = df['cp_charge_increment_df2'].str.replace(',', '.').astype(float)
    df['cp_charging_rate_df2'] = df['cp_charging_rate_df2'].str.replace(',', '.').astype(float)
    df['cp_target_power_df2'] = df['cp_target_power_df2'].str.replace(',', '.').astype(float)

    df['time_minute'] = df['time'] / 60
    df['time_of_day'] = df['time_of_day'] = pd.to_datetime(df['time'], unit='s', origin='2024-01-01').dt.strftime('%H:%M:%S')
    return df

merged_df = preprocess(merged_df)
GRID_LIMIT = 150

# Create Dash app
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

# KPI functions
def calculate_kpis(df, suffix):
    if suffix == 'df1':
        total_energy_used = df['cp_charging_rate_df1'].sum()
        cars_charged = df[df['vehicle_charge_df1'] > 0]['vehicle'].nunique()
        cars_not_charged = df[df['vehicle_charge_df1'] == 0]['vehicle'].nunique()

        last_3_entries = df.groupby('vehicle').tail(3)
        condition = (last_3_entries['cp_charge_increment_df1'] == 0) & \
                    (last_3_entries['cp_charging_rate_df1'] == 0) & \
                    (last_3_entries['cp_target_power_df1'] == 0)
        vehicles_stopped_charging = last_3_entries[condition].groupby('vehicle').filter(lambda x: len(x) == 3)[
            'vehicle'].unique()

        df_stopped_charging = df[df['vehicle'].isin(vehicles_stopped_charging)]
        avg_soc = df_stopped_charging.groupby('vehicle').tail(1)['vehicle_soc_df1'].mean()
        median_soc = df_stopped_charging.groupby('vehicle').tail(1)['vehicle_soc_df1'].median()

    else:
        total_energy_used = df['cp_charging_rate_df2'].sum()
        cars_charged = df[df['vehicle_charge_df2'] > 0]['vehicle'].nunique()
        cars_not_charged = df[df['vehicle_charge_df2'] == 0]['vehicle'].nunique()

        last_3_entries = df.groupby('vehicle').tail(3)
        condition = (last_3_entries['cp_charge_increment_df2'] == 0) & \
                    (last_3_entries['cp_charging_rate_df2'] == 0) & \
                    (last_3_entries['cp_target_power_df2'] == 0)
        vehicles_stopped_charging = last_3_entries[condition].groupby('vehicle').filter(lambda x: len(x) == 3)[
            'vehicle'].unique()

        df_stopped_charging = df[df['vehicle'].isin(vehicles_stopped_charging)]
        avg_soc = df_stopped_charging.groupby('vehicle').tail(1)['vehicle_soc_df2'].mean()
        median_soc = df_stopped_charging.groupby('vehicle').tail(1)['vehicle_soc_df2'].median()

    return total_energy_used, cars_charged, cars_not_charged, avg_soc, median_soc


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
        labelStyle={'display': 'block'}
    ),
    dcc.RadioItems(
        id='view-toggle-infrastructure',
        options=[
            {'label': 'Combined', 'value': 'combined'},
            {'label': 'Separate', 'value': 'separate'}
        ],
        value='combined',
        labelStyle={'display': 'block'}
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
        labelStyle={'display': 'block'}
    ),
    html.Div(id='infrastructure-graph-container', style={'overflowY': 'auto', 'height': '600px'}),
], style={'display': 'flex', 'flexDirection': 'column', 'width': '20%', 'padding': '10px'})

app.layout = html.Div(children=[
                      html.Div(className='row',  # Define the row element
                               children=[
                                  html.Div(className='four columns div-user-controls'),  # Define the left element
                                  html.Div(className='eight columns div-for-charts bg-grey')  # Define the right element
                                  ])
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
        labelStyle={'display': 'block'}
    ),
    dcc.Checklist(
        id='graph-toggle-cars',
        options=[
            {'label': 'Total Energy Used', 'value': 'total_energy'},
            {'label': 'State of Charge', 'value': 'soc'},
            {'label': 'CP Target Power', 'value': 'target_power'},
            {'label': 'CP Charging Rate', 'value': 'charging_rate'},
            {'label': 'Vehicle Capacity', 'value': 'vehicle_capacity'}
        ],
        value=['total_energy'],
        labelStyle={'display': 'block'}
    ),
    html.Div(id='car-graph-container', style={'overflowY': 'auto', 'height': '600px'}),
], style={'display': 'flex', 'flexDirection': 'column', 'width': '20%', 'padding': '10px'})

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
        labelStyle={'display': 'block'}
    ),
    dcc.Checklist(
        id='graph-toggle-stations',
        options=[
            {'label': 'Total Energy Delivered', 'value': 'total_energy'},
            {'label': 'Target Power over the Day', 'value': 'target_power'},
            {'label': 'Charging Rate over the Day', 'value': 'charging_rate'}
        ],
        value=['total_energy'],
        labelStyle={'display': 'block'}
    ),
    html.Div(id='station-graph-container', style={'overflowY': 'auto', 'height': '600px'}),
], style={'display': 'flex', 'flexDirection': 'column', 'width': '20%', 'padding': '10px'})

# Main Layout
app.layout = html.Div([
    html.Div([
        dcc.Link('Dashboard', href='/', style={'padding': '10px'}),
        dcc.Link('Charging Infrastructure', href='/charging-infrastructure', style={'padding': '10px'}),
        dcc.Link('Cars', href='/cars', style={'padding': '10px'}),
        dcc.Link('Charging Station', href='/charging-station', style={'padding': '10px'}),
    ], style={'display': 'flex', 'justifyContent': 'center', 'backgroundColor': '#f0f0f0', 'padding': '10px'}),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content', style={'display': 'flex'})
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/charging-infrastructure':
        return html.Div([
            charging_infrastructure_layout,
            html.Div(id='graphs-infrastructure', style={'width': '80%', 'padding': '20px'})
        ], style={'display': 'flex'})
    elif pathname == '/cars':
        return html.Div([
            cars_layout,
            html.Div(id='graphs-cars', style={'width': '80%', 'padding': '20px'})
        ], style={'display': 'flex'})
    elif pathname == '/charging-station':
        return html.Div([
            charging_station_layout,
            html.Div(id='graphs-station', style={'width': '80%', 'padding': '20px'})
        ], style={'display': 'flex'})
    else:
        return html.Div([
            dashboard_layout,
            html.Div(id='kpis', style={'width': '80%', 'padding': '20px'})
        ], style={'display': 'flex'})


#@app.callback(Output('kpis', 'children'),
#              [Input('data-toggle-infrastructure', 'value')])
#def update_dashboard_kpis(datasets):
#    kpis = []
#    for dataset in datasets:
#        kpi_values = calculate_kpis(df1 if dataset == 'df1' else df2, dataset)
#        kpis.append(html.Div([
#            html.H3(f"KPI Set for {dataset}"),
#            html.P(f"Total Energy Used: {kpi_values[0]}"),
#            html.P(f"Cars Charged: {kpi_values[1]}"),
#            html.P(f"Cars Not Charged: {kpi_values[2]}"),
#            html.P(f"Avg SOC: {kpi_values[3]}%"),
#            html.P(f"Median SOC: {kpi_values[4]}%"),
#        ], style={'margin': '20px', 'padding': '20px', 'border': '1px solid #ddd', 'borderRadius': '5px'}))
#    return kpis

@app.callback(Output('kpis', 'children'),
              Input('url', 'pathname'))
def update_kpis(pathname):
    total_energy_1, cars_charged_1, cars_not_charged_1, avg_soc_1, median_soc_1 = calculate_kpis(merged_df, suffix='df1')
    total_energy_2, cars_charged_2, cars_not_charged_2, avg_soc_2, median_soc_2 = calculate_kpis(merged_df, suffix='df2')

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
        'borderRadius': '15px',
        'overflow': 'hidden',
        'margin': 'auto',
    },
    style_as_list_view = True)



@app.callback(Output('graphs-infrastructure', 'children'),
              [Input('data-toggle-infrastructure', 'value'),
               Input('view-toggle-infrastructure', 'value'),
               Input('graph-toggle-infrastructure', 'value')])
def update_infrastructure_graph(datasets, view, selected_graphs):
    graphs = []
    for dataset in datasets:
        df = df1 if dataset == 'df1' else df2
        if 'total_energy' in selected_graphs:
            graphs.append(dcc.Graph(
                figure=go.Figure(
                    data=[go.Scatter(x=df['time_of_day'], y=df[f'cp_charging_rate_{dataset}'],
                                    mode='lines', name='Total Energy Used')]
                ),
                style={'height': '400px'}
            ))
        if 'target_power' in selected_graphs:
            graphs.append(dcc.Graph(
                figure=go.Figure(
                    data=[go.Scatter(x=df['time_of_day'], y=df[f'cp_target_power_{dataset}'],
                                    mode='lines', name='CP Target Power')]
                ),
                style={'height': '400px'}
            ))
        if 'charging_rate' in selected_graphs:
            graphs.append(dcc.Graph(
                figure=go.Figure(
                    data=[go.Scatter(x=df['time_of_day'], y=df[f'cp_charging_rate_{dataset}'],
                                    mode='lines', name='CP Charging Rate')]
                ),
                style={'height': '400px'}
            ))
        if 'grid_limit' in selected_graphs:
            graphs.append(dcc.Graph(
                figure=go.Figure(
                    data=[go.Scatter(x=df['time_of_day'], y=[GRID_LIMIT] * len(df['time_of_day']),
                                    mode='lines', name='Grid Limit')]
                ),
                style={'height': '400px'}
            ))

    return graphs


@app.callback(Output('graphs-cars', 'children'),
              [Input('car-dropdown', 'value'),
               Input('view-toggle-cars', 'value'),
               Input('graph-toggle-cars', 'value')])
def update_cars_graph(car, view, selected_graphs):
    graphs = []
    df = merged_df[merged_df['vehicle'] == car]
    if 'total_energy' in selected_graphs:
        graphs.append(dcc.Graph(
            figure=go.Figure(
                data=[go.Scatter(x=df['time_of_day'], y=df['cp_charging_rate_df1'],
                                mode='lines', name='Total Energy Used')]
            ),
            style={'height': '400px'}
        ))
    if 'soc' in selected_graphs:
        graphs.append(dcc.Graph(
            figure=go.Figure(
                data=[go.Scatter(x=df['time_of_day'], y=df['vehicle_soc_df1'],
                                mode='lines', name='State of Charge')]
            ),
            style={'height': '400px'}
        ))
    if 'target_power' in selected_graphs:
        graphs.append(dcc.Graph(
            figure=go.Figure(
                data=[go.Scatter(x=df['time_of_day'], y=df['cp_target_power_df1'],
                                mode='lines', name='CP Target Power')]
            ),
            style={'height': '400px'}
        ))
    if 'charging_rate' in selected_graphs:
        graphs.append(dcc.Graph(
            figure=go.Figure(
                data=[go.Scatter(x=df['time_of_day'], y=df['cp_charging_rate_df1'],
                                mode='lines', name='CP Charging Rate')]
            ),
            style={'height': '400px'}
        ))
    if 'vehicle_capacity' in selected_graphs:
        graphs.append(dcc.Graph(
            figure=go.Figure(
                data=[go.Scatter(x=df['time_of_day'], y=[100] * len(df['time_of_day']),
                                mode='lines', name='Vehicle Capacity')]
            ),
            style={'height': '400px'}
        ))
    return graphs


@app.callback(Output('graphs-station', 'children'),
              [Input('station-dropdown', 'value'),
               Input('view-toggle-stations', 'value'),
               Input('graph-toggle-stations', 'value')])
def update_station_graph(station, view, selected_graphs):
    graphs = []
    df = merged_df[merged_df['cp'] == station]
    if 'total_energy' in selected_graphs:
        graphs.append(dcc.Graph(
            figure=go.Figure(
                data=[go.Scatter(x=df['time_of_day'], y=df['cp_charging_rate_df1'],
                                mode='lines', name='Total Energy Delivered')]
            ),
            style={'height': '400px'}
        ))
    if 'target_power' in selected_graphs:
        graphs.append(dcc.Graph(
            figure=go.Figure(
                data=[go.Scatter(x=df['time_of_day'], y=df['cp_target_power_df1'],
                                mode='lines', name='Target Power over the Day')]
            ),
            style={'height': '400px'}
        ))
    if 'charging_rate' in selected_graphs:
        graphs.append(dcc.Graph(
            figure=go.Figure(
                data=[go.Scatter(x=df['time_of_day'], y=df['cp_charging_rate_df1'],
                                mode='lines', name='Charging Rate over the Day')]
            ),
            style={'height': '400px'}
        ))
    return graphs


if __name__ == '__main__':
    app.run_server(debug=True)
