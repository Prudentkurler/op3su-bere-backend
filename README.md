# 🌤️ Weather Analysis API Backend

A powerful Django REST API for weather analysis and geospatial climate data processing. This backend provides comprehensive weather data analysis using NASA POWER API and Meteomatics fallback, compound extreme weather analysis, and geospatial segmentation capabilities.

## 🚀 Features

### Core Weather Analysis
- **Compound Extreme Analysis**: Analyze multiple weather variables simultaneously
- **Historical Data Processing**: 25+ years of weather data analysis
- **Multiple Weather Conditions**: Very hot, very cold, very wet, very windy conditions
- **Probability Calculations**: Statistical analysis of weather pattern occurrence

### Geospatial Analysis
- **Geospatial Segmentation**: Analyze weather patterns across geographic grids
- **Location-based Analysis**: Find similar climate conditions in nearby areas
- **Grid-based Processing**: Configurable resolution and search radius

### Data Sources
- **Primary**: NASA POWER API (free, reliable)
- **Fallback**: Meteomatics API (premium, high accuracy)
- **Automatic Failover**: Seamless switching between data sources
- **Geocoding**: Nominatim OpenStreetMap integration

### API Endpoints
- **Weather Analysis** (`/api/weather/`)
- **Event Management** (`/api/events/`)
- **Geospatial Segmentation** (`/api/geospatial-segmentation/`)
- **Weather Conditions** (`/api/conditions/`)
- **Analysis Summary** (`/api/analysis/summary/`)

## 🛠️ Technology Stack

- **Backend Framework**: Django 5.2.6 + Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT Token-based authentication
- **Weather APIs**: NASA POWER API, Meteomatics API
- **Geocoding**: Nominatim (OpenStreetMap)
- **Python Version**: 3.8+

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <your-new-repo-url>
   cd <your-repo-name>
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   
   # Optional: Meteomatics API (for enhanced accuracy)
   METEOMATICS_USERNAME=your-username
   METEOMATICS_PASSWORD=your-password
   ```

5. **Database setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/`

## 🔧 Configuration

### Weather Data Sources
The system uses a fallback mechanism:
1. **NASA POWER API** (Primary): Free, no authentication required
2. **Meteomatics API** (Fallback): Requires credentials, higher accuracy

### Environment Variables
| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DEBUG` | Django debug mode | No | `False` |
| `SECRET_KEY` | Django secret key | Yes | - |
| `METEOMATICS_USERNAME` | Meteomatics API username | No | - |
| `METEOMATICS_PASSWORD` | Meteomatics API password | No | - |

## 📊 API Documentation

### Weather Analysis
```http
POST /api/weather/
Content-Type: application/json

{
  "location": "Accra",
  "month": 8,
  "day": 15,
  "condition": "very_hot",
  "event_type": "Agricultural Activity"
}
```

### Geospatial Segmentation
```http
POST /api/geospatial-segmentation/
Content-Type: application/json

{
  "location": "Accra",
  "month": 8,
  "condition": "very_hot",
  "step": 0.5,
  "range": 1.0
}
```

### Weather Conditions
```http
GET /api/conditions/
```

See [API_USAGE.md](API_USAGE.md) for complete API documentation.

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Test Weather APIs
```bash
python test_weather_fallback.py
```

## 🚀 Deployment

### Production Setup
1. Set `DEBUG=False` in production
2. Configure proper database (PostgreSQL recommended)
3. Set up static file serving
4. Use production WSGI server (Gunicorn, uWSGI)
5. Set up reverse proxy (Nginx, Apache)

### Docker Deployment
```dockerfile
# Example Dockerfile structure
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "backend.wsgi:application"]
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 📁 Project Structure

```
├── api/                    # Main API application
│   ├── models.py          # Database models
│   ├── views.py           # API endpoints
│   ├── serializers.py     # Data serialization
│   └── utils/             # Utility modules
│       ├── nominatim.py   # Geocoding utilities
│       ├── nasa.py        # NASA API integration
│       ├── meteomatics.py # Meteomatics API integration
│       └── compound_extremes.py # Weather analysis logic
├── backend/               # Django project settings
├── users/                 # User management
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
└── .env.example         # Environment variables template
```

## 🌍 Weather Conditions Supported

- **Very Hot**: High temperature with humidity analysis
- **Very Cold**: Low temperature with wind chill effects
- **Very Wet**: Heavy precipitation analysis
- **Very Windy**: High wind speed conditions
- **Very Uncomfortable**: Composite discomfort index

## 🔗 Related Projects

This backend is designed to work with frontend applications. The API provides:
- RESTful endpoints for all weather analysis features
- JWT authentication for secure access
- Comprehensive error handling and validation
- CORS support for frontend integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the [API_USAGE.md](API_USAGE.md) documentation
- Review the [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help

## 🏆 Acknowledgments

- **NASA POWER API** for free weather data access
- **Meteomatics** for premium weather data services  
- **OpenStreetMap/Nominatim** for geocoding services
- **Django REST Framework** for robust API development