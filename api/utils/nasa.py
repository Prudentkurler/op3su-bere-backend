import requests
from datetime import datetime

# NOTE: This util uses NASA POWER daily point endpoint to retrieve variables.
# Adjust parameters as required. POWER has limits for date ranges; we request by year range.

POWER_ENDPOINT = 'https://power.larc.nasa.gov/api/temporal/daily/point'

# Parameter list we might need
DEFAULT_PARAMETERS = [
    'T2M',        # Daily mean temperature (°C)
    'T2M_MIN',    # Daily min temp
    'T2M_MAX',    # Daily max temp
    'RH2M',       # Relative humidity (%)
    'PRECTOTCORR',# Precipitation total (mm/day)
    'WS10M',      # Wind speed at 10m (m/s)
]


def fetch_power_point(lat, lon, start_year=1995, end_year=2024, parameters=None):
    """
    Fetch NASA POWER data for a specific location and date range
    Returns historical weather data for compound extremes analysis
    """
    parameters = parameters or DEFAULT_PARAMETERS
    params = {
        'latitude': lat,
        'longitude': lon,
        'start': f"{start_year}0101",
        'end': f"{end_year}1231",
        'community': 'RE',
        'parameters': ','.join(parameters),
        'format': 'JSON'
    }
    
    try:
        r = requests.get(POWER_ENDPOINT, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        # data['properties']['parameter'] contains dicts keyed by parameter name
        return data.get('properties', {}).get('parameter', {})
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch NASA POWER data: {str(e)}")


def fetch_historical_data_for_date(lat, lon, target_month, target_day=None, years_back=25):
    """
    Fetch historical data specifically for a target date (month/day) over multiple years
    This optimizes the data fetching for the specific date analysis
    """
    current_year = datetime.now().year
    start_year = current_year - years_back
    
    # Fetch the full year data
    power_data = fetch_power_point(lat, lon, start_year, current_year - 1)
    
    # Filter data for the specific month/day
    filtered_data = {}
    for param_name, param_data in power_data.items():
        filtered_data[param_name] = {}
        
        for date_str, value in param_data.items():
            try:
                dt = datetime.strptime(date_str, '%Y%m%d')
                if dt.month == target_month:
                    if target_day is None or dt.day == target_day:
                        filtered_data[param_name][date_str] = value
            except ValueError:
                continue
    
    return filtered_data
