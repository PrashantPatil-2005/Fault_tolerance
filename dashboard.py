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

# --- Helper Functions (same as before) ---
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

# --- Data Preparation for Table ---
machine_data = get_machine_data()
if machine_data:
    # We create a pandas DataFrame, which is great for tables
    df = pd.DataFrame(machine_data)
    # Select and rename columns for clarity
    df = df[['name', 'dataUpdatedTime', 'healthStatus', '_id']]
    df.columns = ['Machine Name', 'Last Update', 'Health Status', 'id']
    # Format the date to be more readable
    df['Last Update'] = pd.to_datetime(df['Last Update']).dt.strftime('%Y-%m-%d %H:%M:%S')
else:
    df = pd.DataFrame(columns=['Machine Name', 'Last Update', 'Health Status', 'id'])


# --- Initialize the Dash App ---
app = dash.Dash(__name__)
app.title = "AAMS Predictive Maintenance Dashboard"

# --- Define the Layout of the App ---
app.layout = html.Div([
    html.H1("AAMS Predictive Maintenance Dashboard"),
    html.Hr(),
    html.H3("Machine Health Overview"),
    # NEW: Using DataTable to show the main health report
    dash_table.DataTable(
        id='machine-table',
        columns=[{"name": i, "id": i} for i in df.columns if i != 'id'], # Don't display the ID column
        data=df.to_dict('records'),
        row_selectable='single', # Allow user to select one machine
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
        # NEW: Applying color-coding to the 'Health Status' column
        style_data_conditional=[
            {'if': {'filter_query': '{Health Status} = "Alarm"'}, 'backgroundColor': '#FF4136', 'color': 'white'},
            {'if': {'filter_query': '{Health Status} = "Normal"'}, 'backgroundColor': '#FFD700', 'color': 'black'},
            {'if': {'filter_query': '{Health Status} = "Satisfactory"'}, 'backgroundColor': '#2ECC40', 'color': 'white'},
        ]
    ),
    html.Hr(),
    # The dropdown for bearings is now updated by the table selection
    html.H3("Detailed Analysis"),
    html.Div(id='selected-machine-name'),
    dcc.Dropdown(id='bearing-dropdown'),
    dcc.Graph(id='raw-data-graph'),
    dcc.Graph(id='fft-graph')
])

# --- Callbacks to Make the App Interactive ---

# This callback updates the bearing dropdown when a machine is selected in the table
@app.callback(
    Output('bearing-dropdown', 'options'),
    Output('selected-machine-name', 'children'),
    Input('machine-table', 'selected_rows'))
def update_bearing_dropdown(selected_rows):
    if not selected_rows:
        return [], "Please select a machine from the table above."
    
    selected_machine_id = df.iloc[selected_rows[0]]['id']
    selected_machine_name = df.iloc[selected_rows[0]]['Machine Name']
    
    bearing_data = get_bearing_data(selected_machine_id)
    bearing_options = [{'label': i['name'], 'value': i['_id']} for i in bearing_data]
    
    return bearing_options, f"Showing details for: {selected_machine_name}"

# This callback updates the graphs based on the selected bearing
@app.callback(
    Output('raw-data-graph', 'figure'),
    Output('fft-graph', 'figure'),
    Input('bearing-dropdown', 'value'))
def update_graphs(selected_bearing):
    # This function remains largely the same
    if not selected_bearing:
        empty_fig = {'data': [], 'layout': {'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'annotations': [{'text': 'Select a bearing to see its vibration data', 'showarrow': False}]}}
        return empty_fig, empty_fig

    sensor_data = get_sensor_data(selected_bearing)
    if not sensor_data or 'rawData' not in sensor_data:
        error_layout = {'title': 'Error: Could not retrieve sensor data.'}
        return {'data': [], 'layout': error_layout}, {'data': [], 'layout': error_layout}
    
    raw_data = sensor_data.get('rawData', [])
    sampling_rate = float(sensor_data.get('SR', 1))
    
    time_df = pd.DataFrame({'Time (s)': np.arange(len(raw_data)) / sampling_rate, 'Amplitude': raw_data})
    raw_fig = px.line(time_df, x='Time (s)', y='Amplitude', title='Raw Vibration Data (Time Domain)')

    N = len(raw_data)
    T = 1.0 / sampling_rate
    yf = np.fft.fft(raw_data)
    xf = np.fft.fftfreq(N, T)[:N // 2]
    amplitude = 2.0 / N * np.abs(yf[0:N // 2])
    
    fft_df = pd.DataFrame({'Frequency (Hz)': xf, 'Amplitude': amplitude})
    fft_fig = px.line(fft_df, x='Frequency (Hz)', y='Amplitude', title='Frequency Spectrum (FFT)')
    
    return raw_fig, fft_fig

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)