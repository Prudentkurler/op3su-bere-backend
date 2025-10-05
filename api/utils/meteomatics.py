import requests
from datetime import datetime, timedelta
import base64

# Meteomatics API configuration
METEOMATICS_BASE_URL = 'https://api.meteomatics.com'

# Parameter mapping from NASA POWER to Meteomatics
PARAMETER_MAPPING = {
    'T2M': 't_2m:C',           # Daily mean temperature (°C)
    'T2M_MIN': 't_min_2m_24h:C',   # Daily min temp
    'T2M_MAX': 't_max_2m_24h:C',   # Daily max temp
    'RH2M': 'relative_humidity_2m:p',  # Relative humidity (%)
    'PRECTOTCORR': 'precip_24h:mm',    # Precipitation total (mm/day)
    'WS10M': 'wind_speed_10m:ms',      # Wind speed at 10m (m/s)
}


def get_meteomatics_auth_header(username, password):
    """
    Create authorization header for Meteomatics API
    You'll need to set these credentials in your environment or settings
    """
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded_credentials}"


def fetch_meteomatics_data(lat, lon, start_year=1999, end_year=2024, parameters=None, username=None, password=None):
    """
    Fetch historical weather data from Meteomatics API
    Returns data in a format similar to NASA POWER for compatibility
    
    Note: Meteomatics requires authentication credentials
    """
    if not username or not password:
        raise Exception("Meteomatics API requires username and password credentials")
    
    parameters = parameters or list(PARAMETER_MAPPING.keys())
    
    # Convert parameters to Meteomatics format
    meteomatics_params = [PARAMETER_MAPPING.get(p, p) for p in parameters if p in PARAMETER_MAPPING]
    
    if not meteomatics_params:
        raise Exception("No valid parameters mapped for Meteomatics API")
    
    # Meteomatics API format: /start_date--end_date:step/parameters/lat,lon/format
    start_date = f"{start_year}-01-01T00:00:00Z"
    end_date = f"{end_year}-12-31T00:00:00Z"
    
    # Use daily step (P1D)
    time_range = f"{start_date}--{end_date}:P1D"
    param_string = ",".join(meteomatics_params)
    location = f"{lat},{lon}"
    
    url = f"{METEOMATICS_BASE_URL}/{time_range}/{param_string}/{location}/json"
    
    headers = {
        'Authorization': get_meteomatics_auth_header(username, password),
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Convert Meteomatics format to NASA POWER format
        converted_data = convert_meteomatics_to_nasa_format(data, parameters)
        
        return converted_data
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch Meteomatics data: {str(e)}")


def convert_meteomatics_to_nasa_format(meteomatics_data, original_parameters):
    """
    Convert Meteomatics JSON response to NASA POWER format
    Meteomatics returns: {'data': [{'parameter': 'param_name', 'coordinates': [...], 'dates': [...], 'values': [...]}]}
    NASA format: {'param_name': {'YYYYMMDD': value, ...}}
    """
    converted = {}
    
    # Initialize all requested parameters
    for param in original_parameters:
        converted[param] = {}
    
    if 'data' not in meteomatics_data:
        return converted
    
    # Reverse parameter mapping
    reverse_mapping = {v: k for k, v in PARAMETER_MAPPING.items()}
    
    for dataset in meteomatics_data['data']:
        meteomatics_param = dataset.get('parameter')
        nasa_param = reverse_mapping.get(meteomatics_param)
        
        if not nasa_param:
            continue
            
        dates = dataset.get('dates', [])
        values = dataset.get('values', [])
        
        # Convert dates and values
        for date_str, value in zip(dates, values):
            try:
                # Parse Meteomatics date format (ISO format)
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                # Convert to NASA format YYYYMMDD
                nasa_date = dt.strftime('%Y%m%d')
                
                # Handle null/missing values
                if value is not None:
                    converted[nasa_param][nasa_date] = value
                    
            except (ValueError, TypeError):
                continue
    
    return converted


def fetch_meteomatics_historical_data(lat, lon, target_month, target_day=None, years_back=25, username=None, password=None):
    """
    Fetch historical data from Meteomatics for a specific date over multiple years
    Compatible with the NASA function signature
    """
    current_year = datetime.now().year
    start_year = current_year - years_back
    
    # Fetch the full data
    meteomatics_data = fetch_meteomatics_data(
        lat, lon, start_year, current_year - 1, 
        username=username, password=password
    )
    
    # Filter data for the specific month/day (same logic as NASA)
    filtered_data = {}
    for param_name, param_data in meteomatics_data.items():
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


def test_meteomatics_connection(username, password):
    """
    Test connection to Meteomatics API
    """
    try:
        # Simple test query - get current temperature for a known location
        test_url = f"{METEOMATICS_BASE_URL}/now/t_2m:C/40.7128,-74.0060/json"
        headers = {
            'Authorization': get_meteomatics_auth_header(username, password),
            'Content-Type': 'application/json'
        }
        
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return True, "Meteomatics API connection successful"
        
    except requests.exceptions.RequestException as e:
        return False, f"Meteomatics API connection failed: {str(e)}"