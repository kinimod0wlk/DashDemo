import dash
from dash import dcc, html
import plotly.graph_objs as go
import pandas as pd

# Load data from CSV files
df1 = pd.read_csv('result1.csv', delimiter=';')
df2 = pd.read_csv('result2.csv', delimiter=';')
df_test = pd.read_csv('test.csv')

# Preprocess the data to replace commas with dots for numerical values
df1 = df1.replace(',', '.', regex=True).astype(float)
df2 = df2.replace(',', '.', regex=True).astype(float)
df_test = df_test.replace(',', '.', regex=True).astype(float)

# Extracting values
time1 = df1['time']
vehicle_charge1 = df1['vehicle_charge']
time2 = df2['time']
vehicle_charge2 = df2['vehicle_charge']

# Feature: Possible as many points as possible
# Feature: Rename for intuition
# Feature: Target Power >= Charging Rate (Always)
# Feature: Include Grid Limit (Static, from config)
# Assuming grid limit is available as a column in the CSV or defined in config
grid_limit = 50  # Example value, adjust according to your config

# Create traces for each dataset
trace1 = go.Scatter(x=time1, y=vehicle_charge1, mode='markers', name='Vehicle Charge 1')
trace2 = go.Scatter(x=time2, y=vehicle_charge2, mode='lines', name='Vehicle Charge 2')

# Additional feature: Charging Infrastructure (kWh per vehicle, time of charging)
charging_infrastructure = df_test[['arrival_time', 'kwh_capacity', 'kwh_SoC', 'energy_charged']]

# Calculate average instead of sum
average_charge = df1.groupby('vehicle')['vehicle_charge'].mean()

# Fixing time jumps for null values in aggregation
df1['time'] = df1['time'].fillna(method='ffill')

# Calculations for KPIs (Key Performance Indicators)
total_energy_charged = df1['vehicle_charge'].sum()
average_energy_per_vehicle = df1['vehicle_charge'].mean()

# Create a layout for the graph
layout = go.Layout(
    title='Overlaying Diagrams',
    xaxis=dict(title='Time', tickmode='linear', dtick=1),
    yaxis=dict(title='Vehicle Charge'),
    legend=dict(orientation="h"),
    shapes=[
        dict(
            type='line',
            yref='y', y0=grid_limit, y1=grid_limit,
            xref='x', x0=min(time1), x1=max(time1),
            line=dict(dash='dash', width=2)
        )
    ]
)

# Create the figure object
fig = go.Figure(data=[trace1, trace2], layout=layout)

# Create the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    dcc.Graph(figure=fig),
    html.Div(f'Total Energy Charged: {total_energy_charged} kWh'),
    html.Div(f'Average Energy per Vehicle: {average_energy_per_vehicle} kWh')
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
