# Event Management API Documentation

The backend has been updated to support user-defined events with weather analysis and data for frontend AI integration. Here's how to use the new API endpoints:

## New Features

1. **User-defined events** - Users can create custom events instead of hardcoded types
2. **Dynamic weather sensitivity** - Each event can have custom weather conditions it's sensitive to
3. **Data for frontend AI** - Backend provides structured data for frontend Gemini AI integration
4. **Cached analysis** - Weather analysis results are cached to reduce API calls

## API Endpoints

### 1. Event Management

#### Create/List Events
```
POST /api/events/
GET /api/events/
```

**Create Event Example:**
```json
{
  "name": "Beach Wedding",
  "description": "Outdoor wedding ceremony on the beach",
  "event_type": "wedding",
  "location_only": "Santa Monica Beach, CA",
  "target_month": 6,
  "target_day": 15,
  "weather_sensitivity": ["very_hot", "very_wet", "very_windy"]
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Beach Wedding",
  "event_type": "wedding",
  "location_name": "Santa Monica Beach, CA",
  "latitude": 34.0195,
  "longitude": -118.4912,
  "target_date_display": "June 15",
  "weather_sensitivity": ["very_hot", "very_wet", "very_windy"],
  "created_at": "2024-10-04T20:30:00Z"
}
```

#### Get/Update/Delete Specific Event
```
GET /api/events/{id}/
PUT /api/events/{id}/
DELETE /api/events/{id}/
```

### 2. Weather Analysis

#### Run Weather Analysis for Event
```
POST /api/events/analyze/
```

**Request:**
```json
{
  "event_id": 1,
  "conditions": ["very_hot", "very_wet"],
  "force_refresh": false
}
```

#### Direct Weather Query (Legacy)
```
POST /api/weather/
```

**Request:**
```json
{
  "location": "Santa Monica Beach, CA",
  "month": 6,
  "day": 15,
  "condition": "very_hot",
  "event_type": "wedding"
}
```
**Note:** Both `month` and `day` are required fields for weather queries.

**Response:**
```json
{
  "event": {
    "id": 1,
    "name": "Beach Wedding",
    "target_date_display": "June 15"
  },
  "analysis_results": {
    "very_hot": {
      "probability": 23.5,
      "condition_description": "High temperature with humidity",
      "years_total": 25,
      "years_matching": 6,
      "variables_analyzed": ["T2M", "RH2M", "T2M_MIN"],
      "thresholds": {
        "T2M": 32.0,
        "RH2M": 70.0,
        "T2M_MIN": 22.0
      }
    },
    "very_wet": {
      "probability": 15.2,
      "condition_description": "Heavy precipitation",
      "years_total": 25,
      "years_matching": 4
    }
  },
  "cached": false,
  "last_updated": "2024-10-04T20:35:00Z"
}
```

### 3. Data for Frontend AI Integration

#### Get Event Data for AI Processing
```
POST /api/events/ai-data/
```

**Request:**
```json
{
  "event_id": 1,
  "include_analysis": true
}
```

**Response:**
```json
{
  "event": {
    "id": 1,
    "name": "Beach Wedding",
    "event_type": "wedding",
    "description": "Outdoor wedding ceremony on the beach",
    "location": {
      "name": "Santa Monica Beach, CA",
      "latitude": 34.0195,
      "longitude": -118.4912
    },
    "date": {
      "month": 6,
      "day": 15,
      "display": "June 15"
    },
    "weather_sensitivity": ["very_hot", "very_wet", "very_windy"]
  },
  "analysis": {
    "results": {
      "very_hot": {
        "probability": 23.5,
        "condition_description": "High temperature with humidity"
      }
    },
    "last_updated": "2024-10-04T20:35:00Z",
    "conditions_analyzed": ["very_hot", "very_wet"]
  },
  "available_conditions": {
    "very_hot": {
      "description": "High temperature with humidity",
      "variables": ["T2M", "RH2M", "T2M_MIN"]
    },
    "very_wet": {
      "description": "Heavy precipitation",
      "variables": ["PRECTOTCORR"]
    }
  }
}
```

#### Get Event Summary
```
GET /api/events/{event_id}/summary/
```

**Response:**
```json
{
  "event": {
    "id": 1,
    "name": "Beach Wedding",
    "target_date_display": "June 15"
  },
  "analysis_available": true,
  "analysis_results": {...},
  "weather_context": [
    {
      "condition": "very_hot",
      "description": "High temperature with humidity",
      "probability": 23.5,
      "risk_level": "LOW"
    }
  ]
}
```

## Frontend Integration

The frontend can now:

1. **Create custom events** with user-defined types and weather sensitivity
2. **Run weather analysis** on demand or use cached results
3. **Get structured data** for AI prompting via `/api/events/ai-data/`
4. **Pass the structured data to Gemini AI** in the frontend

## Example Frontend Flow

1. User creates event: `POST /api/events/`
2. User requests analysis: `POST /api/events/analyze/`
3. Frontend gets AI data: `POST /api/events/ai-data/`
4. Frontend sends structured data to Gemini AI with custom prompts
5. AI provides recommendations based on event details and weather analysis

## Available Weather Conditions

- `very_hot`: High temperature with humidity
- `very_cold`: Low temperature with wind chill
- `very_wet`: Heavy precipitation
- `very_windy`: High wind speeds
- `very_uncomfortable`: Heat + humidity + low breeze discomfort

## Authentication

All event endpoints require user authentication via JWT tokens:

```
Authorization: Bearer <your_jwt_token>
```