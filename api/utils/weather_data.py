import logging
from django.conf import settings
from .nasa import fetch_historical_data_for_date as fetch_nasa_data
from .meteomatics import fetch_meteomatics_historical_data
import os

# Configure logging
logger = logging.getLogger(__name__)

def get_meteomatics_credentials():
    """
    Get Meteomatics credentials from environment variables or Django settings
    """
    username = getattr(settings, 'METEOMATICS_USERNAME', None) or os.getenv('METEOMATICS_USERNAME')
    password = getattr(settings, 'METEOMATICS_PASSWORD', None) or os.getenv('METEOMATICS_PASSWORD')
    
    return username, password


def fetch_weather_data_with_fallback(lat, lon, target_month, target_day=None, years_back=25):
    """
    Fetch historical weather data with NASA POWER as primary source and Meteomatics as fallback
    
    Args:
        lat (float): Latitude
        lon (float): Longitude  
        target_month (int): Target month (1-12)
        target_day (int, optional): Target day (1-31)
        years_back (int): Number of years to fetch historical data
        
    Returns:
        tuple: (data, source) where data is the weather data dict and source is 'nasa' or 'meteomatics'
        
    Raises:
        Exception: If both NASA and Meteomatics APIs fail
    """
    
    # First, try NASA POWER API
    try:
        logger.info(f"Attempting to fetch weather data from NASA POWER for lat={lat}, lon={lon}")
        nasa_data = fetch_nasa_data(lat, lon, target_month, target_day, years_back)
        
        # Validate that we got meaningful data
        if nasa_data and any(len(param_data) > 0 for param_data in nasa_data.values()):
            logger.info("Successfully fetched data from NASA POWER")
            return nasa_data, 'nasa'
        else:
            logger.warning("NASA POWER returned empty data, trying fallback")
            raise Exception("NASA POWER returned empty data")
            
    except Exception as nasa_error:
        logger.warning(f"NASA POWER failed: {str(nasa_error)}")
        
        # Try Meteomatics as fallback
        try:
            username, password = get_meteomatics_credentials()
            
            if not username or not password:
                raise Exception("Meteomatics credentials not configured. Please set METEOMATICS_USERNAME and METEOMATICS_PASSWORD environment variables or Django settings.")
            
            logger.info(f"Attempting to fetch weather data from Meteomatics fallback for lat={lat}, lon={lon}")
            meteomatics_data = fetch_meteomatics_historical_data(
                lat, lon, target_month, target_day, years_back, 
                username=username, password=password
            )
            
            # Validate that we got meaningful data
            if meteomatics_data and any(len(param_data) > 0 for param_data in meteomatics_data.values()):
                logger.info("Successfully fetched data from Meteomatics fallback")
                return meteomatics_data, 'meteomatics'
            else:
                raise Exception("Meteomatics returned empty data")
                
        except Exception as meteomatics_error:
            logger.error(f"Meteomatics fallback also failed: {str(meteomatics_error)}")
            
            # Both APIs failed, raise comprehensive error
            raise Exception(
                f"Both weather data sources failed. "
                f"NASA POWER error: {str(nasa_error)}. "
                f"Meteomatics fallback error: {str(meteomatics_error)}"
            )


def get_available_weather_sources():
    """
    Check which weather data sources are available
    
    Returns:
        dict: Status of each weather source
    """
    sources = {
        'nasa': {'available': True, 'message': 'NASA POWER API (Primary)'},
        'meteomatics': {'available': False, 'message': 'Not configured'}
    }
    
    # Check Meteomatics credentials
    username, password = get_meteomatics_credentials()
    if username and password:
        sources['meteomatics'] = {'available': True, 'message': 'Meteomatics API (Fallback)'}
    else:
        sources['meteomatics']['message'] = 'Credentials not configured'
    
    return sources


def test_weather_sources():
    """
    Test connectivity to all weather data sources
    
    Returns:
        dict: Test results for each source
    """
    results = {}
    
    # Test NASA POWER
    try:
        # Simple test - fetch a small amount of recent data
        test_data = fetch_nasa_data(40.7128, -74.0060, 1, 1, 1)  # NYC, January 1st, 1 year back
        if test_data:
            results['nasa'] = {'status': 'success', 'message': 'NASA POWER API is working'}
        else:
            results['nasa'] = {'status': 'warning', 'message': 'NASA POWER returned empty data'}
    except Exception as e:
        results['nasa'] = {'status': 'error', 'message': f'NASA POWER failed: {str(e)}'}
    
    # Test Meteomatics
    try:
        username, password = get_meteomatics_credentials()
        if username and password:
            from .meteomatics import test_meteomatics_connection
            is_connected, message = test_meteomatics_connection(username, password)
            results['meteomatics'] = {
                'status': 'success' if is_connected else 'error',
                'message': message
            }
        else:
            results['meteomatics'] = {
                'status': 'error', 
                'message': 'Meteomatics credentials not configured'
            }
    except Exception as e:
        results['meteomatics'] = {'status': 'error', 'message': f'Meteomatics test failed: {str(e)}'}
    
    return results


def log_weather_data_usage(source, lat, lon, success=True, error_message=None):
    """
    Log usage statistics for weather data sources
    """
    log_message = f"Weather data fetch from {source.upper()} for location ({lat}, {lon})"
    
    if success:
        logger.info(f"{log_message} - SUCCESS")
    else:
        logger.error(f"{log_message} - FAILED: {error_message}")


# Backwards compatibility - maintain the same function name as the original NASA module
def fetch_historical_data_for_date(lat, lon, target_month, target_day=None, years_back=25):
    """
    Backwards compatible function that uses the fallback mechanism
    """
    data, source = fetch_weather_data_with_fallback(lat, lon, target_month, target_day, years_back)
    log_weather_data_usage(source, lat, lon, success=True)
    return data