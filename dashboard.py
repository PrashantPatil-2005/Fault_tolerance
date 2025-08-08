import dash
from dash import dcc, html, Input, Output, dash_table, State
import plotly.graph_objects as go
import plotly.express as px # <--- FIX: Re-added the missing import
import pandas as pd
import requests
import numpy as np
import json
from datetime import datetime

# --- OFFLINE MODE ---
OFFLINE_MODE = True

# --- API and Configuration (for Live Mode) ---
API_BASE_URL = "https://srcapiv2.aams.io/AAMS/AI"
REQUEST_TIMEOUT = 15

# --- Helper Functions ---
def get_machine_data():
    if OFFLINE_MODE:
        try:
            with open('machines.json', 'r') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return []
    try:
        response = requests.post(f"{API_BASE_URL}/Machine", json={}, timeout=REQUEST_TIMEOUT)
        return response.json()
    except requests.exceptions.RequestException: return []

def get_bearing_data(machine_id):
    if OFFLINE_MODE:
        try:
            with open('bearings.json', 'r') as f:
                all_bearings = json.load(f)
                return all_bearings.get(machine_id, [])
        except (FileNotFoundError, json.JSONDecodeError): return []
    try:
        payload = {"machineId": machine_id}
        response = requests.post(f"{API_BASE_URL}/BearingLocation", json=payload, timeout=REQUEST_TIMEOUT)
        return response.json()
    except requests.exceptions.RequestException: return []

def get_sensor_data(bearing_id):
    if OFFLINE_MODE:
        try:
            with open('sensor_snapshot_data.json', 'r') as f:
                all_sensor_data = json.load(f)
                return all_sensor_data.get(bearing_id)
        except (FileNotFoundError, json.JSONDecodeError): return None
    try:
        payload = {"bearingLocationId": bearing_id, "Axis_Id": "H-Axis", "type": "OFFLINE", "Analytics_Types": "MF"}
        response = requests.post(f"{API_BASE_URL}/Data", json=payload, timeout=REQUEST_TIMEOUT)
        return response.json()
    except requests.exceptions.RequestException: return None

def get_historical_data(bearing_id):
    if OFFLINE_MODE:
        try:
            with open('sensor_historical_data.json', 'r') as f:
                all_historical_data = json.load(f)
                return all_historical_data.get(bearing_id)
        except (FileNotFoundError, json.JSONDecodeError): return None
    return None

# --- Data Preparation & App Initialization ---
machine_data = get_machine_data()
df_machines = pd.DataFrame(machine_data)
if not df_machines.empty:
    df_machines = df_machines[['name', 'dataUpdatedTime', 'healthStatus', '_id']]
    df_machines.columns = ['Machine Name', 'Last Update', 'Health Status', 'id']
    df_machines['Last Update'] = pd.to_datetime(df_machines['Last Update']).dt.strftime('%Y-%m-%d %H:%M:%S')

app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
app.title = "AAMS Predictive Maintenance Dashboard"

# --- Layout ---
app.layout = html.Div([
    html.Div([html.H1("AAMS Predictive Maintenance Dashboard", style={'textAlign': 'center'}), html.H4("(Offline Mode)" if OFFLINE_MODE else "(Live Mode)", style={'textAlign': 'center', 'color': 'red' if OFFLINE_MODE else 'green'})], className='row'),
    html.Div([html.H4("Machine Health Overview"), dash_table.DataTable(id='machine-table', columns=[{"name": i, "id": i} for i in df_machines.columns if i != 'id'], data=df_machines.to_dict('records'), row_selectable='single', style_cell={'textAlign': 'left'}, style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}, style_data_conditional=[{'if': {'filter_query': '{Health Status} = "Alarm"'}, 'backgroundColor': '#FF4136', 'color': 'white'}, {'if': {'filter_query': '{Health Status} = "Normal"'}, 'backgroundColor': '#FFD700', 'color': 'black'}, {'if': {'filter_query': '{Health Status} = "Satisfactory"'}, 'backgroundColor': '#2ECC40', 'color': 'white'}])], className='row', style={'marginTop': '20px'}),
    html.Div([html.H4("Detailed Check-up"), html.P(id='selected-machine-name'), dash_table.DataTable(id='bearing-table', columns=[{'name': 'Bearing Name', 'id': 'Bearing Name'}, {'name': 'Health Status', 'id': 'Health Status'}], data=[], row_selectable='single', style_cell={'textAlign': 'left'}, style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}, style_data_conditional=[{'if': {'filter_query': '{Health Status} = "Alarm"'}, 'backgroundColor': '#FF4136', 'color': 'white'}, {'if': {'filter_query': '{Health Status} = "Normal"'}, 'backgroundColor': '#FFD700', 'color': 'black'}, {'if': {'filter_query': '{Health Status} = "Satisfactory"'}, 'backgroundColor': '#2ECC40', 'color': 'white'}])], className='row', style={'marginTop': '20px'}),
    html.Div([html.H4("Historical Health Trend (30 Days)"), dcc.Graph(id='historical-trend-graph')], className='row', style={'marginTop': '20px'}),
    html.Div([html.H4("Vibration Analysis (Snapshot)"), html.Div(id='bearing-parameters-display'), dcc.Graph(id='raw-data-graph'), dcc.Graph(id='fft-graph')], className='row', style={'marginTop': '20px'}),
], className='container')

# --- Callbacks ---
@app.callback(Output('bearing-table', 'data'), Output('selected-machine-name', 'children'), Input('machine-table', 'selected_rows'), State('machine-table', 'data'))
def update_bearing_table(selected_rows, machine_table_data):
    if not selected_rows: return [], "Please select a machine from the table above."
    selected_machine_row = machine_table_data[selected_rows[0]]
    selected_machine_id = selected_machine_row['id']
    selected_machine_name = selected_machine_row['Machine Name']
    bearing_data = get_bearing_data(selected_machine_id)
    if not bearing_data: return [], f"No bearing data available for: {selected_machine_name}"
    df_bearings = pd.DataFrame(bearing_data)[['name', 'healthStatus', '_id']]
    df_bearings.columns = ['Bearing Name', 'Health Status', 'id']
    return df_bearings.to_dict('records'), f"Showing details for: {selected_machine_name}"

@app.callback(Output('historical-trend-graph', 'figure'), Input('bearing-table', 'selected_rows'), State('bearing-table', 'data'))
def update_historical_graph(selected_rows, bearing_data):
    if not selected_rows: return {'data': [], 'layout': {'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'annotations': [{'text': 'Select a bearing to see its historical trend', 'showarrow': False}]}}
    selected_bearing_id = bearing_data[selected_rows[0]]['id']
    historical_data = get_historical_data(selected_bearing_id)
    if not historical_data: return {'data': [], 'layout': {'title': {'text': 'No Historical Data Available for this Bearing'}}}
    df_hist = pd.DataFrame(historical_data)
    df_hist['date'] = pd.to_datetime(df_hist['date'])
    fig = px.line(df_hist, x='date', y='alarmValue', title='Vibration Alarm Value Trend', labels={'date': 'Date', 'alarmValue': 'Alarm Value'})
    fig.update_layout(hovermode='x unified')
    return fig

@app.callback(Output('raw-data-graph', 'figure'), Output('fft-graph', 'figure'), Output('bearing-parameters-display', 'children'), Input('bearing-table', 'selected_rows'), State('bearing-table', 'data'))
def update_snapshot_graphs(selected_rows, bearing_data):
    empty_fig = {'data': [], 'layout': {'xaxis': {'visible': False}, 'yaxis': {'visible': False}, 'annotations': [{'text': 'Select a bearing to see its vibration data', 'showarrow': False}]}}
    if not selected_rows: return empty_fig, empty_fig, []
    selected_bearing_row = bearing_data[selected_rows[0]]
    selected_bearing_id = selected_bearing_row['id']
    sensor_data = get_sensor_data(selected_bearing_id)
    if not sensor_data or 'rawData' not in sensor_data:
        error_layout = {'title': {'text': f"No Snapshot Data Available for {selected_bearing_row['Bearing Name']}"}}
        return {'data': [], 'layout': error_layout}, {'data': [], 'layout': error_layout}, []
    raw_data = sensor_data.get('rawData', [])
    sampling_rate = float(sensor_data.get('SR', 1))
    rpm = sensor_data.get('rpm', 'N/A')
    fmax = sensor_data.get('fMax', 'N/A')
    graph_title = f"Vibration Data for: {selected_bearing_row['Bearing Name']}"
    parameters_display = html.Div([html.B("RPM: "), f"{rpm}", html.Br(), html.B("Sampling Rate (SR): "), f"{sampling_rate} Hz", html.Br(), html.B("Max Frequency (fMax): "), f"{fmax} Hz"], style={'padding': '10px', 'border': '1px solid lightgrey', 'marginBottom': '10px'})
    time_values = np.arange(len(raw_data)) / sampling_rate
    raw_fig = go.Figure(data=go.Scatter(x=time_values, y=raw_data, mode='lines'))
    raw_fig.update_layout(title=f"{graph_title} (Time Domain)", xaxis_title="Time (s)", yaxis_title="Amplitude", hovermode='x unified')
    N = len(raw_data); T = 1.0 / sampling_rate; yf = np.fft.fft(raw_data); xf = np.fft.fftfreq(N, T)[:N // 2]; amplitude = 2.0 / N * np.abs(yf[0:N // 2])
    fft_fig = go.Figure(data=go.Scatter(x=xf, y=amplitude, mode='lines'))
    fft_fig.update_layout(title=f"{graph_title} (Frequency Spectrum)", xaxis_title="Frequency (Hz)", yaxis_title="Amplitude", hovermode='x unified')
    return raw_fig, fft_fig, parameters_display

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)