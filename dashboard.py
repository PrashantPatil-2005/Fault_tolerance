import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import requests
import numpy as np

# --- Configuration ---
# FIX 1: Using the correct API base URL from the documentation
API_BASE_URL = "https://srcapiv2.aams.io/AAMS/AI"

# --- Helper Functions to Get Data from API ---
# Note: The API documentation specifies POST requests, but for simple GETs without a body,
# a POST can sometimes work if the server is configured for it.
# We'll use POST as specified.

def get_machine_data():
    """Fetches the list of all machines."""
    try:
        # The documentation specifies POST, so we send an empty json payload.
        response = requests.post(f"{API_BASE_URL}/Machine", json={})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching machine data: {e}")
        return []

def get_bearing_data(machine_id):
    """Fetches bearing locations for a specific machine."""
    try:
        payload = {"machineId": machine_id}
        response = requests.post(f"{API_BASE_URL}/BearingLocation", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bearing data for machine {machine_id}: {e}")
        return []

def get_sensor_data(bearing_location_id, axis="H-Axis"):
    """Fetches sensor data for a specific bearing."""
    try:
        # Based on the jupyter notebook, the payload needs these fields
        payload = {
            "bearingLocationId": bearing_location_id,
            "Axis_Id": axis,
            "type": "OFFLINE",
            "Analytics_Types": "MF"
        }
        response = requests.post(f"{API_BASE_URL}/Data", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sensor data for bearing {bearing_location_id}: {e}")
        return None

# --- Initialize the Dash App ---
app = dash.Dash(__name__)
app.title = "AAMS Predictive Maintenance Dashboard"

# --- Define the Layout of the App ---
# Fetch initial machine data for the dropdown
machine_options = [{'label': i['name'], 'value': i['_id']} for i in get_machine_data()]

app.layout = html.Div([
    html.H1("AAMS Predictive Maintenance Dashboard"),
    html.Hr(),
    html.Div([
        html.Div([
            html.Label("Select Machine:"),
            dcc.Dropdown(id='machine-dropdown', options=machine_options),
        ], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([
            html.Label("Select Bearing Location:"),
            dcc.Dropdown(id='bearing-dropdown'),
        ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ]),
    html.Hr(),
    html.H3("Vibration Analysis"),
    dcc.Graph(id='raw-data-graph'),
    dcc.Graph(id='fft-graph')
])

# --- Callbacks to Make the App Interactive ---
@app.callback(
    Output('bearing-dropdown', 'options'),
    Input('machine-dropdown', 'value'))
def set_bearing_options(selected_machine):
    if not selected_machine:
        return []
    bearing_data = get_bearing_data(selected_machine)
    return [{'label': i['name'], 'value': i['_id']} for i in bearing_data]

@app.callback(
    Output('raw-data-graph', 'figure'),
    Output('fft-graph', 'figure'),
    Input('bearing-dropdown', 'value'))
def update_graphs(selected_bearing):
    if not selected_bearing:
        empty_fig = {'data': [], 'layout': {'xaxis': {'visible': False}, 'yaxis': {'visible': False}}}
        return empty_fig, empty_fig

    sensor_data = get_sensor_data(selected_bearing)
    if not sensor_data or 'rawData' not in sensor_data:
        return {'data': [], 'layout': {'title': 'No Data Available'}}, {'data': [], 'layout': {'title': 'No Data Available'}}

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
    # FIX 2: Using the new command to run the app
    app.run(debug=True)