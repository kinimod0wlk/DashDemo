import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd

# Load data from CSV files
df1 = pd.read_csv('result1.csv', delimiter=';')
df2 = pd.read_csv('result2.csv', delimiter=';')

GRID_LIMIT = 1000

# Convert columns
def preprocess(df):

    # CSV 1
    df['time'] = df['time'].astype(int)
    df['vehicle'] = df['vehicle'].astype(str)
    df['vehicle_soc'] = df['vehicle_soc'].str.replace(',', '.').astype(float)
    df['vehicle_charge'] = df['vehicle_charge'].str.replace(',', '.').astype(float)
    df['vehicle_capacity'] = df['vehicle_capacity'].str.replace(',', '.').astype(float)
    df['cp_charge_increment'] = df['cp_charge_increment'].str.replace(',', '.').astype(float)
    df['cp_charging_rate'] = df['cp_charging_rate'].str.replace(',', '.').astype(float)
    df['cp_target_power'] = df['cp_target_power'].str.replace(',', '.').astype(float)

    # CSV 2
    df['vehicle_soc_second'] = df['vehicle_soc_second'].str.replace(',', '.').astype(float)
    df['vehicle_charge_second'] = df['vehicle_charge_second'].str.replace(',', '.').astype(float)
    df['vehicle_capacity_second'] = df['vehicle_capacity_second'].str.replace(',', '.').astype(float)
    df['cp_charge_increment_second'] = df['cp_charge_increment_second'].str.replace(',', '.').astype(float)
    df['cp_charging_rate_second'] = df['cp_charging_rate_second'].str.replace(',', '.').astype(float)
    df['cp_target_power_second'] = df['cp_target_power_second'].str.replace(',', '.').astype(float)

    df['time_minute'] = df['time'] / 60
    df['time_of_day'] = pd.to_datetime(df['time_minute'], unit='m', origin='2024-01-01').dt.strftime('%H:%M')
    return df

df2 = df2.rename(columns=lambda x: x + '_second' if x not in ['time', 'vehicle'] else x)

df1_sorted = df1.sort_values(['vehicle', 'time'])
df2_sorted = df2.sort_values(['vehicle', 'time'])

merged_df = pd.merge(df1_sorted, df2_sorted, on=['vehicle', 'time'], how='outer', suffixes=('', '_second'))

all_columns = [col for col in merged_df.columns if col not in ['time', 'vehicle']]

vehicles_seen = set()
for idx, row in merged_df.iterrows():
    vehicle = row['vehicle']
    if vehicle not in vehicles_seen:
        vehicles_seen.add(vehicle)
    else:
        for col in all_columns:
            if pd.isnull(row[col]):
                if 'cp_charge_increment' in col:
                    merged_df.at[idx, col] = 0
                else:
                    previous_values = merged_df.loc[(merged_df['vehicle'] == vehicle) & (merged_df.index < idx), col].ffill().bfill()
                    if not previous_values.empty:
                        previous_value = previous_values.iloc[-1]
                        merged_df.at[idx, col] = previous_value

merged_df.to_csv('merged_result_corrected.csv', index=False, sep=';')
processed_merge = preprocess(merged_df)
merged_df = processed_merge


# Create Dash app
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

# KPI functions
def calculate_kpis(df, suffix=''):
    suffix = str(suffix)  # Ensure suffix is always a string
    if (suffix.__eq__('')):
        total_energy_used = df['cp_charging_rate'].sum()
        cars_charged = df[df['vehicle_charge'] > 0]['vehicle'].nunique()
        cars_not_charged = df[df['vehicle_charge'] == 0]['vehicle'].nunique()

        last_3_entries = df.groupby('vehicle').tail(3)
        condition = (last_3_entries['cp_charge_increment'] == 0) & \
                    (last_3_entries['cp_charging_rate'] == 0) & \
                    (last_3_entries['cp_target_power'] == 0)
        vehicles_stopped_charging = last_3_entries[condition].groupby('vehicle').filter(lambda x: len(x) == 3)['vehicle'].unique()

        df_stopped_charging = df[df['vehicle'].isin(vehicles_stopped_charging)]
        avg_soc = df_stopped_charging.groupby('vehicle').tail(1)['vehicle_soc'].mean()
        median_soc = df_stopped_charging.groupby('vehicle').tail(1)['vehicle_soc'].median()

    else:
        total_energy_used = df['cp_charging_rate_second'].sum()
        cars_charged = df[df['vehicle_charge_second'] > 0]['vehicle'].nunique()
        cars_not_charged = df[df['vehicle_charge_second'] == 0]['vehicle'].nunique()

        last_3_entries = df.groupby('vehicle').tail(3)
        condition = (last_3_entries['cp_charge_increment_second'] == 0) & \
                    (last_3_entries['cp_charging_rate_second'] == 0) & \
                    (last_3_entries['cp_target_power_second'] == 0)
        vehicles_stopped_charging = last_3_entries[condition].groupby('vehicle').filter(lambda x: len(x) == 3)['vehicle'].unique()

        df_stopped_charging = df[df['vehicle'].isin(vehicles_stopped_charging)]
        avg_soc = df_stopped_charging.groupby('vehicle').tail(1)['vehicle_soc_second'].mean()
        median_soc = df_stopped_charging.groupby('vehicle').tail(1)['vehicle_soc_second'].median()

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
            {'label': 'CP Charging Rate', 'value': 'charging_rate'},
            {'label': 'Vehicle Capacity', 'value': 'vehicle_capacity'}
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


@app.callback(Output('kpis', 'children'),
              Input('url', 'pathname'))
def update_kpis(pathname):
    total_energy_1, cars_charged_1, cars_not_charged_1, avg_soc_1, median_soc_1 = calculate_kpis(merged_df)
    total_energy_2, cars_charged_2, cars_not_charged_2, avg_soc_2, median_soc_2 = calculate_kpis(merged_df, suffix='_second')
    data = [
        {'KPI': 'Total Energy Used (kWh)', 'Dataset 1': total_energy_1, 'Dataset 2': total_energy_2},
        {'KPI': 'Cars Charged', 'Dataset 1': cars_charged_1, 'Dataset 2': cars_charged_2},
        {'KPI': 'Cars Not Charged', 'Dataset 1': cars_not_charged_1, 'Dataset 2': cars_not_charged_2},
        {'KPI': 'Average SoC', 'Dataset 1': avg_soc_1, 'Dataset 2': avg_soc_2},
        {'KPI': 'Median SoC', 'Dataset 1': median_soc_1, 'Dataset 2': median_soc_2},
    ]
    columns = [
        {'name': 'KPI', 'id': 'KPI'},
        {'name': 'Dataset 1', 'id': 'Dataset 1'},
        {'name': 'Dataset 2', 'id': 'Dataset 2'}
    ]
    return dash_table.DataTable(data=data, columns=columns, style_table={'width': '100%', 'overflowX': 'auto'})

@app.callback(
    Output('infrastructure-graph-container', 'children'),
    [Input('data-toggle-infrastructure', 'value'),
     Input('view-toggle-infrastructure', 'value'),
     Input('graph-toggle-infrastructure', 'value')]
)
def update_infrastructure_graph(data_toggle, view_toggle, graph_toggle):
    traces = []

    def create_traces(df, dataset_name, suffix, line_style):
        trace_list = []
        if 'total_energy' in graph_toggle:
            df_sorted = df.sort_values(by='time_of_day')
            total_energy = df_sorted.groupby('time_of_day')[f'cp_charging_rate{suffix}'].sum().cumsum()
            trace_list.append(go.Bar(x=total_energy.index, y=total_energy, name=f'{dataset_name} - Cumulative Total Energy Used'))
        if 'target_power' in graph_toggle:
            target_power = df.groupby('time_of_day')[f'cp_target_power{suffix}'].mean()
            trace_list.append(go.Scatter(x=target_power.index, y=target_power, mode='lines', name=f'{dataset_name} - CP Target Power', line=line_style))
        if 'charging_rate' in graph_toggle:
            charging_rate = df.groupby('time_of_day')[f'cp_charging_rate{suffix}'].mean()
            trace_list.append(go.Scatter(x=charging_rate.index, y=charging_rate, mode='lines', name=f'{dataset_name} - CP Charging Rate', line=line_style))
        if 'grid_limit' in graph_toggle:
            trace_list.append(go.Scatter(x=df['time_of_day'].unique(), y=[GRID_LIMIT]*len(df['time_of_day'].unique()), mode='lines', name='Grid Limit', line={'dash': 'dash'}))
        return trace_list

    if view_toggle == 'combined':
        if 'df1' in data_toggle:
            traces.extend(create_traces(merged_df, 'Dataset 1', '', {'dash': 'solid'}))
        if 'df2' in data_toggle:
            traces.extend(create_traces(merged_df, 'Dataset 2', '_second', {'dash': 'solid'}))
        layout = go.Layout(
            title='Charging Infrastructure Data',
            xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
            yaxis={'title': 'Value', 'tickformat': ',.0f'},
            barmode='group',
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
        )
        return [dcc.Graph(figure=go.Figure(data=traces, layout=layout))]
    else:
        graphs = []
        if 'df1' in data_toggle:
            traces = create_traces(merged_df, 'Dataset 1', '', {'dash': 'solid'})
            layout = go.Layout(
                title='Charging Infrastructure Data (Dataset 1)',
                xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
                yaxis={'title': 'Value', 'tickformat': ',.0f'},
                barmode='group',
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
            )
            graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))
        if 'df2' in data_toggle:
            traces = create_traces(merged_df, 'Dataset 2', '_second', {'dash': 'solid'})
            layout = go.Layout(
                title='Charging Infrastructure Data (Dataset 2)',
                xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
                yaxis={'title': 'Value', 'tickformat': ',.0f'},
                barmode='group',
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
            )
            graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))
        return graphs

@app.callback(
    Output('car-graph-container', 'children'),
    [Input('car-dropdown', 'value'),
     Input('view-toggle-cars', 'value'),
     Input('graph-toggle-cars', 'value')]
)
def update_car_graph(selected_car, view_toggle, graph_toggle):
    df1_filtered = merged_df[merged_df['vehicle'] == selected_car]
    df2_filtered = merged_df[merged_df['vehicle'] == selected_car]

    def get_initial_soc(df, suffix):
        initial_soc_row = df[df['vehicle'] == selected_car].sort_values(by='time_of_day').iloc[0]
        return float(initial_soc_row[f'vehicle_charge{suffix}'])

    def create_traces(df, dataset_name, suffix, line_style, initial_soc):
        trace_list = []
        if 'soc' in graph_toggle:
            soc = df.groupby('time_of_day')[f'cp_charge_increment{suffix}'].sum().cumsum() + initial_soc
            trace_list.append(go.Scatter(x=soc.index, y=soc, mode='lines', name=f'{dataset_name} - State of Charge', line=line_style))
        if 'target_power' in graph_toggle:
            target_power = df.groupby('time_of_day')[f'cp_target_power{suffix}'].mean()
            trace_list.append(go.Scatter(x=target_power.index, y=target_power, mode='lines', name=f'{dataset_name} - CP Target Power', line=line_style))
        if 'charging_rate' in graph_toggle:
            charging_rate = df.groupby('time_of_day')[f'cp_charging_rate{suffix}'].mean()
            trace_list.append(go.Scatter(x=charging_rate.index, y=charging_rate, mode='lines', name=f'{dataset_name} - CP Charging Rate', line=line_style))
        return trace_list

    if view_toggle == 'combined':
        traces = []
        if not df1_filtered.empty:
            initial_soc_1 = get_initial_soc(merged_df, '')
            traces.extend(create_traces(df1_filtered, 'Dataset 1', '', {'dash': 'solid'}, initial_soc_1))
        if not df2_filtered.empty:
            initial_soc_2 = get_initial_soc(merged_df, '_second')
            traces.extend(create_traces(df2_filtered, 'Dataset 2', '_second', {'dash': 'solid'}, initial_soc_2))
        layout = go.Layout(
            title=f'Car Data - {selected_car}',
            xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
            yaxis={'title': 'Value', 'tickformat': ',.0f'},
            barmode='group',
            legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
        )
        return [dcc.Graph(figure=go.Figure(data=traces, layout=layout))]
    else:
        graphs = []
        if not df1_filtered.empty:
            traces = create_traces(df1_filtered, 'Dataset 1', '', {'dash': 'solid'}, get_initial_soc(merged_df, ''))
            layout = go.Layout(
                title=f'Car Data (Dataset 1) - {selected_car}',
                xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
                yaxis={'title': 'Value', 'tickformat': ',.0f'},
                barmode='group',
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
            )
            graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))
        if not df2_filtered.empty:
            traces = create_traces(df2_filtered, 'Dataset 2', '_second', {'dash': 'solid'}, get_initial_soc(merged_df, '_second'))
            layout = go.Layout(
                title=f'Car Data (Dataset 2) - {selected_car}',
                xaxis={'title': 'Time of Day', 'tickformat': '%H:%M'},
                yaxis={'title': 'Value', 'tickformat': ',.0f'},
                barmode='group',
                legend=dict(orientation='h', xanchor='right', x=1, y=-0.2)
            )
            graphs.append(dcc.Graph(figure=go.Figure(data=traces, layout=layout)))
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

