# Fault Tolerance Dashboard for Predictive Maintenance

## Overview

This project is an interactive web dashboard designed for the predictive maintenance of industrial machinery. It visualizes real-time and historical vibration data to help engineers identify potential equipment faults before they lead to costly failures.

The dashboard is built with Python using the Dash framework and can operate in two modes:

* **Offline Mode**: Uses local JSON files for data, which is ideal for development and demonstration without requiring an internet connection.
* **Live Mode**: Connects directly to the AAMS.io API to fetch live sensor data.

---

## Features

* **Machine Health Overview**: A color-coded table provides an at-a-glance view of the health status (`Alarm`, `Normal`, `Satisfactory`) of all monitored machines.
* **Drill-Down Analysis**: Users can select a specific machine to view the health of its individual bearings.
* **Historical Trend Analysis**: Plots the historical vibration alarm values for a selected bearing, making it easy to spot degrading performance over time.
* **Vibration Analysis Snapshot**: For any selected bearing, the dashboard displays:
    * **Key Metrics**: Crucial time-domain features like RMS, Peak, and Kurtosis.
    * **Time-Domain Plot**: A graph of the raw vibration signal.
    * **Frequency Spectrum (FFT)**: An FFT plot to pinpoint specific fault frequencies related to imbalance, misalignment, or bearing defects.

---

## Project Structure

The project is organized into a modular structure for clarity and maintainability:

```
├── data/                     # Contains sample data for offline mode
│   ├── machines.json
│   ├── bearings.json
|   ├── sensor_snapshot_data.json
│   └── sensor_historical_data.json
├── assets/                   # CSS stylesheets for the dashboard
│   └── style.css
├── app.py                    # Main Dash application layout and callbacks
├── analysis.py               # Functions for data analysis (FFT, RMS, etc.)
├── api_client.py             # Functions for fetching data (API or local)
├── .gitignore                # Files to be ignored by Git
├── README.md                 # This file
└── requirements.txt          # Python libraries required for the project
```

---

## Getting Started

Follow these steps to set up and run the dashboard on your local machine.

### Prerequisites

* Python 3.7+
* `pip` package manager

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/PrashantPatil-2005/Fault_tolerance.git
    cd fault_tolerance_dashboard
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    # For Windows
    python -m venv venv
    venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1.  Make sure you are in the project's root directory and your virtual environment is activated.

2.  Run the main application file from your terminal:
    ```bash
    python app.py
    ```

3.  Open your web browser and navigate to the following address:
    `http://127.0.0.1:8050/`

---

## Configuration

The dashboard can be switched between **Offline** and **Live** modes by editing the `OFFLINE_MODE` variable in both `app.py` and `api_client.py`.

* To run using local JSON data, set the variable to `True`.
* To connect to the live AAMS.io API, set the variable to `False`.

```python
# In app.py and api_client.py
OFFLINE_MODE = True # Set to False for live data
