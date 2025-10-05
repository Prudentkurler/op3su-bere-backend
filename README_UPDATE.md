# Weather App - Setup Instructions

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd Op3su-bere
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Create environment file from template
cp .env.example .env

# Edit .env with your settings (optional Meteomatics credentials)
# nano .env

# Run migrations and start server
python manage.py migrate
python manage.py runserver 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm start  # Runs on port 3001
```

## 🌦️ Weather Data Sources

This app uses **NASA POWER** as the primary weather data source with **Meteomatics** as an optional fallback:

- **NASA POWER**: Free, no configuration needed ✅
- **Meteomatics**: Paid service, optional for redundancy ⚠️

### Adding Meteomatics (Optional)
1. Sign up at [Meteomatics](https://www.meteomatics.com/)
2. Add credentials to your `.env` file:
   ```env
   METEOMATICS_USERNAME=your_username
   METEOMATICS_PASSWORD=your_password
   ```

## 🔧 Configuration Files

- **`.env`**: Local environment variables (not committed to Git)
- **`.env.example`**: Template for environment variables
- **`WEATHER_CONFIG.md`**: Detailed weather API configuration
- **`DEPLOYMENT.md`**: Production deployment guide

## 🧪 Testing

Test your weather data setup:
```bash
# Test the fallback mechanism
python test_weather_fallback.py

# Check API endpoints
curl http://localhost:8000/api/weather-sources/status/
curl -X POST http://localhost:8000/api/weather-sources/test/
```

## 📝 Key Features

- ✅ NASA POWER weather data (primary)
- ✅ Meteomatics fallback (optional)
- ✅ Automatic failover between APIs
- ✅ Environment-based configuration
- ✅ Comprehensive logging
- ✅ Status monitoring endpoints

## 🚀 Deployment

The app is ready for deployment on any platform. See `DEPLOYMENT.md` for specific instructions for:
- Heroku
- DigitalOcean
- AWS
- Railway
- Vercel
- Self-hosted VPS

## 🔒 Security

- All sensitive data uses environment variables
- No hardcoded API keys or secrets
- `.env` file is excluded from Git
- Production and development configurations are separate

This setup ensures your app works locally without any API keys, but gives you the option to add Meteomatics for production redundancy!