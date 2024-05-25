import dash
from dash import dcc, html
import plotly.graph_objs as go
import pandas as pd

# Load data from CSV files
df1 = pd.read_csv('result1.csv', delimiter=';')
#df2 = pd.read_csv('result2.csv', delimiter=';')

print(df1.columns)
#print(df2.columns)


# Assuming CSV files have columns 'x' and 'y' for both datasets
x_values1 = df1['vehicle']
y_values1 = df1['vehicle_charge']
#x_values2 = df2['vehicle']
#y_values2 = df2['vehicle_charge']

# Create traces for each dataset
trace1 = go.Scatter(x=x_values1, y=y_values1, mode='markers', name='Diagram 1')
#trace2 = go.Scatter(x=x_values2, y=y_values2, mode='lines', name='Diagram 2')

# Create a data list with both traces
data = [trace1]
#data = [trace1, trace2]

# Create a layout for the graph
layout = go.Layout(title='Overlaying Diagrams',
                   xaxis=dict(title='X-axis'),
                   yaxis=dict(title='Y-axis'))

# Create the figure object
fig = go.Figure(data=data, layout=layout)

# Create the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    dcc.Graph(figure=fig)
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

## Load data from CSV files
#df1 = pd.read_csv('test.csv')
#df2 = pd.read_csv('test.csv')
#
## Assuming CSV files have columns 'x' and 'y' for both datasets
#x_values1 = df1['visited_company']
#y_values1 = df1['waiting_time']
#x_values2 = df2['visited_company']
#y_values2 = df2['waiting_time']
#
## Create traces for each dataset
#trace1 = go.Scatter(x=x_values1, y=y_values1, mode='lines', name='Diagram 1')
#trace2 = go.Scatter(x=x_values2, y=y_values2, mode='lines', name='Diagram 2')
#
## Create a data list with both traces
#data = [trace1, trace2]
#
## Create a layout for the graph
#layout = go.Layout(title='Overlaying Diagrams',
#                   xaxis=dict(title='X-axis'),
#                   yaxis=dict(title='Y-axis'))
#
## Create the figure object
#fig = go.Figure(data=data, layout=layout)
#
## Create the Dash app
#app = dash.Dash(__name__)
#
## Define the layout of the app
#app.layout = html.Div([
#    dcc.Graph(figure=fig)
#])
#
## Run the app
#if __name__ == '__main__':
#    app.run_server(debug=True)
# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

## Load data from CSV files
#df1 = pd.read_csv('test.csv')
#df2 = pd.read_csv('test.csv')
#
## Assuming CSV files have columns 'x' and 'y' for both datasets
#x_values1 = df1['visited_company']
#y_values1 = df1['waiting_time']
#x_values2 = df2['visited_company']
#y_values2 = df2['waiting_time']
#
## Create traces for each dataset
#trace1 = go.Scatter(x=x_values1, y=y_values1, mode='lines', name='Diagram 1')
#trace2 = go.Scatter(x=x_values2, y=y_values2, mode='lines', name='Diagram 2')
#
## Create a data list with both traces
#data = [trace1, trace2]
#
## Create a layout for the graph
#layout = go.Layout(title='Overlaying Diagrams',
#                   xaxis=dict(title='X-axis'),
#                   yaxis=dict(title='Y-axis'))
#
## Create the figure object
#fig = go.Figure(data=data, layout=layout)
#
## Create the Dash app
#app = dash.Dash(__name__)
#
## Define the layout of the app
#app.layout = html.Div([
#    dcc.Graph(figure=fig)
#])
#
## Run the app
#if __name__ == '__main__':
#    app.run_server(debug=True)