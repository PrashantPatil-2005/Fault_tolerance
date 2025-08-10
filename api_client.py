import json
import requests

# --- Configuration ---
OFFLINE_MODE = True
API_BASE_URL = "https://srcapiv2.aams.io/AAMS/AI"
REQUEST_TIMEOUT = 30

def get_machine_data():
    if OFFLINE_MODE:
        try:
            with open('data/machines.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
            
    try:
        # --- MODIFICATION START ---
        # The server times out on empty requests {}.
        # We will send a filtered request that is known to work,
        # asking for machines with a "Satisfactory" status by default.
        payload = {
            "status": "Satisfactory"
        }
        # --- MODIFICATION END ---
        
        print(f"Fetching data from API with filter: {payload}")
        
        response = requests.post(
            f"{API_BASE_URL}/Machine", 
            json=payload, 
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}") 
        return []

def get_bearing_data(machine_id):
    if OFFLINE_MODE:
        try:
            with open('data/bearings.json', 'r') as f:
                all_bearings = json.load(f)
                return all_bearings.get(machine_id, [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    try:
        # This payload matches the working curl command format
        payload = {"machineId": machine_id}
        response = requests.post(
            f"{API_BASE_URL}/BearingLocation", 
            json=payload, 
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []

def get_sensor_data(bearing_id):
    if OFFLINE_MODE:
        try:
            with open('data/sensor_snapshot_data.json', 'r') as f:
                all_sensor_data = json.load(f)
                return all_sensor_data.get(bearing_id)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    try:
        # This payload matches the working curl command format
        payload = {"bearingLocationId": bearing_id, "Axis_Id": "H-Axis", "type": "OFFLINE", "Analytics_Types": "MF"}
        response = requests.post(
            f"{API_BASE_URL}/Data", 
            json=payload, 
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def get_historical_data(bearing_id):
    if OFFLINE_MODE:
        try:
            with open('data/sensor_historical_data.json', 'r') as f:
                all_historical_data = json.load(f)
                return all_historical_data.get(bearing_id)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    # This function would need a live API endpoint defined
    return None