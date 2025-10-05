import requests

USER_AGENT = "ClimeSenseApp/1.0 (+https://example.com)"

def geocode(place_name, limit=1):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': place_name,
        'format': 'json',
        'limit': limit
    }
    headers = {'User-Agent': USER_AGENT}
    r = requests.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    if not data:
        return None
    item = data[0]
    return {
        'lat': float(item['lat']),
        'lon': float(item['lon']),
        'display_name': item.get('display_name')
    }

def reverse_geocode(lat, lon):
    url = 'https://nominatim.openstreetmap.org/reverse'
    params = {'lat': lat, 'lon': lon, 'format': 'json'}
    headers = {'User-Agent': USER_AGENT}
    r = requests.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get('display_name')
