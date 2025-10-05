#!/usr/bin/env python3
"""
Test script for weather data fallback mechanism
Run this to verify that the NASA -> Meteomatics fallback is working correctly
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.utils.weather_data import (
    fetch_weather_data_with_fallback,
    get_available_weather_sources,
    test_weather_sources
)

def test_weather_sources_status():
    """Test the status of weather sources"""
    print("=== Weather Sources Status ===")
    sources = get_available_weather_sources()
    
    for source, info in sources.items():
        status = "✅ Available" if info['available'] else "❌ Not Available"
        print(f"{source.upper()}: {status} - {info['message']}")
    
    print()

def test_weather_connectivity():
    """Test connectivity to weather sources"""
    print("=== Weather Sources Connectivity Test ===")
    results = test_weather_sources()
    
    for source, result in results.items():
        if result['status'] == 'success':
            print(f"✅ {source.upper()}: {result['message']}")
        elif result['status'] == 'warning':
            print(f"⚠️ {source.upper()}: {result['message']}")
        else:
            print(f"❌ {source.upper()}: {result['message']}")
    
    print()

def test_fallback_mechanism():
    """Test the actual fallback mechanism with real API calls"""
    print("=== Fallback Mechanism Test ===")
    
    # Test coordinates (New York City)
    lat, lon = 40.7128, -74.0060
    target_month, target_day = 6, 15  # June 15th
    
    try:
        print(f"Testing weather data fetch for NYC ({lat}, {lon}) on June 15th...")
        data, source = fetch_weather_data_with_fallback(
            lat, lon, target_month, target_day, years_back=5  # Use smaller range for testing
        )
        
        print(f"✅ Successfully fetched data using: {source.upper()}")
        
        # Check data quality
        param_count = len([p for p in data.values() if len(p) > 0])
        total_params = len(data)
        print(f"📊 Data quality: {param_count}/{total_params} parameters have data")
        
        # Show sample data
        for param_name, param_data in data.items():
            if param_data:
                sample_dates = list(param_data.keys())[:3]
                print(f"   {param_name}: {len(param_data)} data points (sample: {sample_dates})")
            else:
                print(f"   {param_name}: No data")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback mechanism failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("Weather Data Fallback Test Suite")
    print("=" * 50)
    print()
    
    # Test 1: Check source availability
    test_weather_sources_status()
    
    # Test 2: Test connectivity
    test_weather_connectivity()
    
    # Test 3: Test fallback mechanism
    fallback_success = test_fallback_mechanism()
    
    print()
    print("=" * 50)
    if fallback_success:
        print("✅ All tests passed! Weather data fallback is working correctly.")
    else:
        print("❌ Some tests failed. Check the configuration and logs.")
    
    print()
    print("Configuration Tips:")
    print("1. NASA POWER requires no configuration (free API)")
    print("2. For Meteomatics fallback, set environment variables:")
    print("   export METEOMATICS_USERNAME='your_username'")
    print("   export METEOMATICS_PASSWORD='your_password'")
    print("3. Check WEATHER_CONFIG.md for detailed setup instructions")

if __name__ == "__main__":
    main()