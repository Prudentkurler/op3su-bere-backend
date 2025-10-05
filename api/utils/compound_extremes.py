from datetime import datetime

# Enhanced conditions with detailed variables and thresholds
CONDITIONS = {
    'very_hot': {
        'variables': ['T2M', 'RH2M', 'T2M_MIN'],
        'thresholds': {
            'T2M': 32.0,      # Daily mean temperature (°C)
            'RH2M': 70.0,     # Relative humidity (%)
            'T2M_MIN': 22.0   # Night minimum temperature (°C)
        },
        'logic': 'and',  # Require temperature AND humidity to exceed thresholds
        'display_name': 'Very Hot',
        'description': 'High temperature with humidity'
    },
    'very_cold': {
        'variables': ['T2M_MIN', 'WS10M', 'T2M'],
        'thresholds': {
            'T2M_MIN': 5.0,   # Daily minimum temperature (°C)
            'WS10M': 5.0,     # Wind speed at 10m (m/s) for wind chill
            'T2M': 7.0         # Daily mean temperature (°C)
        },
        'logic': 'at_least_2',  # At least 2 of 3 variables must exceed thresholds
        'display_name': 'Very Cold',
        'description': 'Low temperature with wind chill effects'
    },
    'very_wet': {
        'variables': ['PRECTOTCORR'],
        'thresholds': {
            'PRECTOTCORR': 20.0  # Daily precipitation (mm/day)
        },
        'logic': 'single',  # Single variable threshold
        'display_name': 'Very Wet',
        'description': 'Heavy precipitation'
    },
    'very_windy': {
        'variables': ['WS10M'],
        'thresholds': {
            'WS10M': 10.0  # Wind speed at 10m (m/s)
        },
        'logic': 'single',  # Single variable threshold
        'display_name': 'Very Windy',
        'description': 'High wind speed'
    },
    'very_uncomfortable': {
        'variables': ['T2M', 'RH2M', 'WS10M', 'PRECTOTCORR'],
        'thresholds': {
            'T2M': 30.0,        # Temperature (°C)
            'RH2M': 65.0,       # Humidity (%)
            'WS10M': 3.0,       # Low wind speed (m/s) - creates stickiness
            'PRECTOTCORR': 1.0  # Low precipitation threshold
        },
        'logic': 'composite',  # Composite discomfort index
        'display_name': 'Very Uncomfortable',
        'description': 'Heat + humidity + low breeze discomfort'
    }
}

# Event types and their weather sensitivity
EVENT_TYPES = {
    'funeral': {
        'sensitive_to': ['very_hot', 'very_cold', 'very_wet', 'very_windy'],
        'description': 'Outdoor ceremonies sensitive to extreme weather'
    },
    'wedding': {
        'sensitive_to': ['very_hot', 'very_cold', 'very_wet', 'very_windy'],
        'description': 'Outdoor ceremonies and photos sensitive to weather'
    },
    'hiking': {
        'sensitive_to': ['very_hot', 'very_cold', 'very_wet', 'very_windy'],
        'description': 'Outdoor activity highly dependent on weather conditions'
    },
    'picnic': {
        'sensitive_to': ['very_hot', 'very_cold', 'very_wet', 'very_windy'],
        'description': 'Outdoor gathering sensitive to weather'
    },
    'sports_event': {
        'sensitive_to': ['very_hot', 'very_cold', 'very_wet', 'very_windy'],
        'description': 'Outdoor sports events affected by weather'
    },
    'festival': {
        'sensitive_to': ['very_hot', 'very_cold', 'very_wet', 'very_windy'],
        'description': 'Outdoor festivals sensitive to weather conditions'
    }
}


def month_filtered_values(parameter_series, target_month, target_day=None):
    """parameter_series is a dict with date keys YYYYMMDD -> value"""
    vals_by_year = []
    for date_str, val in parameter_series.items():
        try:
            dt = datetime.strptime(date_str, '%Y%m%d')
        except Exception:
            continue
        
        # Filter by month
        if dt.month == target_month:
            # If specific day is provided, filter by day as well
            if target_day is None or dt.day == target_day:
                vals_by_year.append((dt.year, val))
    
    return vals_by_year


def calculate_composite_score(year_data, condition_cfg):
    """Calculate composite discomfort score for very_uncomfortable condition"""
    score = 0
    weights = {'T2M': 0.3, 'RH2M': 0.3, 'WS10M': 0.2, 'PRECTOTCORR': 0.2}
    
    for var in condition_cfg['variables']:
        val = year_data.get(var)
        thresh = condition_cfg['thresholds'].get(var)
        
        if val is not None and thresh is not None:
            if var == 'WS10M':  # Low wind is uncomfortable
                if val < thresh:
                    score += weights[var] * (thresh - val) / thresh
            else:  # High temp, humidity, precip are uncomfortable
                if val > thresh:
                    score += weights[var] * (val - thresh) / thresh
    
    return score


def calculate_probability(power_params, target_month, target_day, condition_key, event_type=None):
    """
    Calculate probability of weather condition occurring on specific date
    Returns detailed analysis including variables, years, and percentages
    """
    cfg = CONDITIONS.get(condition_key)
    if not cfg:
        raise ValueError(f'Unknown condition: {condition_key}')

    # Collect values for each variable by year
    var_year_vals = {}
    years = set()
    
    for var in cfg['variables']:
        series = power_params.get(var, {})
        filtered = month_filtered_values(series, target_month, target_day)
        var_year_vals[var] = {year: val for year, val in filtered}
        years.update(v[0] for v in filtered)

    years = sorted(years)
    if not years:
        return {
            'probability': 0.0,
            'years_total': 0,
            'years_matching': 0,
            'years_sampled': [],
            'variables_analyzed': cfg['variables'],
            'thresholds': cfg['thresholds'],
            'condition_description': cfg['description'],
            'event_type': event_type,
            'event_sensitivity': EVENT_TYPES.get(event_type, {}).get('sensitive_to', []) if event_type else []
        }

    match_count = 0
    total_count = 0
    matching_years = []
    year_details = []

    for y in years:
        total_count += 1
        year_data = {var: var_year_vals.get(var, {}).get(y) for var in cfg['variables']}
        
        # Apply logic based on condition type
        logic = cfg['logic']
        matched = False
        
        if logic == 'and':
            # All variables must exceed thresholds
            checks = []
            for var in cfg['variables']:
                val = year_data.get(var)
                thresh = cfg['thresholds'].get(var)
                if val is not None and thresh is not None:
                    checks.append(val > thresh)
                else:
                    checks.append(False)
            matched = all(checks)
            
        elif logic == 'at_least_2':
            # At least 2 variables must exceed thresholds
            checks = []
            for var in cfg['variables']:
                val = year_data.get(var)
                thresh = cfg['thresholds'].get(var)
                if val is not None and thresh is not None:
                    checks.append(val > thresh)
                else:
                    checks.append(False)
            matched = sum(1 for c in checks if c) >= 2
            
        elif logic == 'single':
            # Any variable exceeds threshold
            matched = any(
                year_data.get(var) is not None and 
                cfg['thresholds'].get(var) is not None and 
                year_data.get(var) > cfg['thresholds'].get(var)
                for var in cfg['variables']
            )
            
        elif logic == 'composite':
            # Composite score calculation
            score = calculate_composite_score(year_data, cfg)
            matched = score > 0.5  # Threshold for discomfort

        if matched:
            match_count += 1
            matching_years.append(y)
        
        # Store year details for analysis
        year_details.append({
            'year': y,
            'values': year_data,
            'matched': matched
        })

    probability = match_count / total_count if total_count else 0.0
    
    return {
        'probability': round(probability * 100, 2),
        'years_total': total_count,
        'years_matching': match_count,
        'years_sampled': years,
        'matching_years': matching_years,
        'variables_analyzed': cfg['variables'],
        'thresholds': cfg['thresholds'],
        'condition_description': cfg['description'],
        'event_type': event_type,
        'event_sensitivity': EVENT_TYPES.get(event_type, {}).get('sensitive_to', []) if event_type else [],
        'year_details': year_details
    }
