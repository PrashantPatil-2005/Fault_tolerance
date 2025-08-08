import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import pandas as pd
import requests
import numpy as np
from datetime import datetime

# --- Configuration ---
API_BASE_URL = "https://srcapiv2.aams.io/AAMS/AI"
REQUEST_TIMEOUT = 15

# --- Helper Functions (No changes here) ---
def get_machine_data():
    try:
        response = requests.post(f"{API_BASE_URL}/Machine", json={}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching machine data: {e}")
        return []

def get_bearing_data(machine_id):
    try:
        payload = {"machineId": machine_id}
        response = requests.post(f"{API_BASE_URL}/BearingLocation", json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bearing data: {e}")
        return []

def get_sensor_data(bearing_location_id, axis="H-Axis"):
    try:
        payload = {"bearingLocationId": bearing_location_id, "Axis_Id": axis, "type": "OFFLINE", "Analytics_Types": "MF"}
        response = requests.post(f"{API_BASE_URL}/Data", json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sensor data: {e}")
        return None

# --- Data Preparation for Machine Table ---
machine_data = get_machine_data()
if machine_data:
    df_machines = pd.DataFrame(machine_data)
    df_machines = df_machines[['name', 'dataUpdatedTime', 'healthStatus', '_id']]
    df_machines.columns = ['Machine Name', 'Last Update', 'Health Status', 'id']
    df_machines['Last Update'] = pd.to_datetime(df_machines['Last Update']).dt.strftime('%Y-%m-%d %H:%M:%S')
else:
    df_machines = pd.DataFrame(columns=['Machine Name', 'Last Update', 'Health Status', 'id'])

# --- Initialize the Dash App ---
app = dash.Dash(__name__)
app.title = "AAMS Predictive Maintenance Dashboard"

# --- Define the Layout of the App ---
app.layout = html.Div([
    html.H1("AAMS Predictive Maintenance Dashboard"),
    html.Hr(),
    html.H3("Machine Health Overview"),
    dash_table.DataTable(
        id='machine-table',
        columns=[{"name": i, "id": i} for i in df_machines.columns if i != 'id'],
        data=df_machines.to_dict('records'),
        row_selectable='single',
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
        style_data_conditional=[
            {'if': {'filter_query': '{Health Status} = "Alarm"'}, 'backgroundColor': '#FF4136', 'color': 'white'},
            {'if': {'filter_query': '{Health Status} = "Normal"'}, 'backgroundColor': '#FFD700', 'color': 'black'},
            {'if': {'filter_query': '{Health Status} = "Satisfactory"'}, 'backgroundColor': '#2ECC40', 'color': 'white'},
        ]
    ),
    html.Hr(),
    html.H3("Detailed Check-up"),
    html.Div(id='selected-machine-name'),
    # NEW: A table to show the bearings of the selected machine
    dash_table.DataTable(
        id='bearing-table',
        columns=[
            {'name': 'Bearing Name', 'id': 'Bearing Name'},
            {'name': 'Health Status', 'id': 'Health Status'}
        ],
        data=[], # Initially empty
        row_selectable='single',
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
        style_data_conditional=[ # Color-coding for this table as well
            {'if': {'filter_query': '{Health Status} = "Alarm"'}, 'backgroundColor': '#FF4136', 'color': 'white'},
            {'if': {'filter_query': '{Health Status} = "Normal"'}, 'backgroundColor': '#FFD700', 'color': 'black'},
            {'if': {'filter_query': '{Health Status} = "Satisfactory"'}, 'backgroundColor': '#2ECC40', 'color': 'white'},
        ]
    ),
    html.Hr(),
    html.H3("Vibration Analysis"),
    dcc.Graph(id='raw-data-graph'),
    dcc.Graph(id='fft-graph')
], style={'fontFamily': 'Arial, sans-serif'})

# --- Callbacks to Make the App Interactive ---

# Callback to update the bearing table based on machine selection
@app.callback(
    Output('bearing-table', 'data'),
    Output('selected-machine-name', 'children'),
    Input('machine-table', 'selected_rows'))
def update_bearing_table(selected_rows):
    if not selected_rows:
        return [], "Please select a machine from the table above."
    
    selected_machine_id = df_machines.iloc[selected_rows[0]]['id']
    selected_machine_name = df_machines.iloc[selected_rows[0]]['Machine Name']
    
    bearing_data = get_bearing_data(selected_machine_id)
    if not bearing_data:
        return [], f"No bearing data available for: {selected_machine_name}"

    df_bearings = pd.DataFrame(bearing_data)
    df_bearings = df_bearings[['name', 'healthStatus', '_id']]
    df_bearings.columns = ['Bearing Name', 'Health Status', 'id']
    
    return df_bearings.to_dict('records'), f"Showing details for: {selected_machine_name}"

# Callback to update graphs based on bearing selection from the new table
@app.callback(
    Output('raw-data-graph', 'figure'),
    Output('fft-graph', 'figure'),
    Input('bearing-table', 'selected_rows'),
    # We also need the full bearing data from the previous callback
    dash.dependencies.State('bearing-table', 'data'))
def update_graphs(selected_rows, bearing_data):
    if not selected_rows:
        empty_fig = {'data': [], 'layout': {'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'annotations': [{'text': 'Select a bearing to see its vibration data', 'showarrow': False}]}}
        return empty_fig, empty_fig

    selected_bearing_row = bearing_data[selected_rows[0]]
    selected_bearing_id = selected_bearing_row['id']
    
    sensor_data = get_sensor_data(selected_bearing_id)
    if not sensor_data or 'rawData' not in sensor_data:
        error_layout = {'title': f"Error: Could not retrieve data for {selected_bearing_row['Bearing Name']}."}
        return {'data': [], 'layout': error_layout}, {'data': [], 'layout': error_layout}
    
    raw_data = sensor_data.get('rawData', [])
    sampling_rate = float(sensor_data.get('SR', 1))
    graph_title = f"Vibration Data for: {selected_bearing_row['Bearing Name']}"
    
    time_df = pd.DataFrame({'Time (s)': np.arange(len(raw_data)) / sampling_rate, 'Amplitude': raw_data})
    raw_fig = px.line(time_df, x='Time (s)', y='Amplitude', title=f"{graph_title} (Time Domain)")

    N = len(raw_data)
    T = 1.0 / sampling_rate
    yf = np.fft.fft(raw_data)
    xf = np.fft.fftfreq(N, T)[:N // 2]
    amplitude = 2.0 / N * np.abs(yf[0:N // 2])
    
    fft_df = pd.DataFrame({'Frequency (Hz)': xf, 'Amplitude': amplitude})
    fft_fig = px.line(fft_df, x='Frequency (Hz)', y='Amplitude', title=f"{graph_title} (Frequency Spectrum)")
    
    return raw_fig, fft_fig

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)