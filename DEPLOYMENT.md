# Deployment Guide

This guide covers how to deploy your weather app with proper environment variable management across different platforms.

## 🏠 Local Development

### 1. Setup `.env` file
Copy the example file and fill in your values:
```bash
cp .env.example .env
```

Edit `.env` with your actual values:
```env
# Django Settings
DEBUG=True
SECRET_KEY=your-super-secret-key-here

# Meteomatics API (Optional - for weather data fallback)
METEOMATICS_USERNAME=your_meteomatics_username
METEOMATICS_PASSWORD=your_meteomatics_password
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Locally
```bash
python manage.py migrate
python manage.py runserver
```

---

## 🌐 Production Deployment

### Option 1: Heroku

**Setting Environment Variables:**
```bash
# Set via Heroku CLI
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set DEBUG=False
heroku config:set METEOMATICS_USERNAME="your-username"
heroku config:set METEOMATICS_PASSWORD="your-password"

# Or via Heroku Dashboard:
# Go to App → Settings → Config Vars
```

**Additional Heroku Setup:**
1. Create `Procfile`:
   ```
   web: gunicorn backend.wsgi
   ```

2. Add gunicorn to `requirements.txt`:
   ```
   gunicorn
   ```

3. Update `ALLOWED_HOSTS` in settings or set via env:
   ```bash
   heroku config:set ALLOWED_HOSTS="your-app-name.herokuapp.com"
   ```

### Option 2: DigitalOcean App Platform

**Setting Environment Variables:**
1. In DigitalOcean Dashboard → Apps → Your App
2. Go to Settings → App-Level Environment Variables
3. Add:
   ```
   SECRET_KEY = your-secret-key
   DEBUG = False
   METEOMATICS_USERNAME = your-username
   METEOMATICS_PASSWORD = your-password
   ALLOWED_HOSTS = your-domain.com
   ```

### Option 3: AWS Elastic Beanstalk

**Setting Environment Variables:**
1. Via AWS Console:
   - Elastic Beanstalk → Environment → Configuration → Software
   - Add Environment Properties

2. Via EB CLI:
   ```bash
   eb setenv SECRET_KEY="your-secret-key" DEBUG=False METEOMATICS_USERNAME="your-username" METEOMATICS_PASSWORD="your-password"
   ```

### Option 4: Google Cloud Run

**Setting Environment Variables:**
```bash
gcloud run deploy --set-env-vars SECRET_KEY="your-secret-key",DEBUG=False,METEOMATICS_USERNAME="your-username",METEOMATICS_PASSWORD="your-password"
```

### Option 5: Railway

**Setting Environment Variables:**
1. Railway Dashboard → Your Project → Variables
2. Add each environment variable:
   ```
   SECRET_KEY = your-secret-key
   DEBUG = False
   METEOMATICS_USERNAME = your-username
   METEOMATICS_PASSWORD = your-password
   ```

### Option 6: Vercel

**Setting Environment Variables:**
1. Vercel Dashboard → Project → Settings → Environment Variables
2. Add variables for Production, Preview, and Development environments

### Option 7: Microsoft Azure App Service

**Prerequisites:**
- Azure account with an active subscription
- Azure CLI installed locally (optional but recommended)
- PostgreSQL database (Azure Database for PostgreSQL or external)

**Step 1: Create Azure App Service**
1. Log into Azure Portal
2. Create a new App Service:
   ```bash
   # Using Azure CLI
   az webapp create --resource-group myResourceGroup --plan myAppServicePlan --name your-app-name --runtime "PYTHON|3.11"
   ```
   Or use the Azure Portal to create manually

**Step 2: Set Environment Variables in Azure**
1. Go to App Service → Configuration → Application Settings
2. Add these environment variables:
   ```
   SECRET_KEY = your-generated-secret-key
   DEBUG = False
   ALLOWED_HOSTS = your-app-name.azurewebsites.net
   DATABASE_URL = postgresql://username:password@host:port/database
   FRONTEND_URL = https://your-frontend-domain.com
   METEOMATICS_USERNAME = your-username (optional)
   METEOMATICS_PASSWORD = your-password (optional)
   DJANGO_SUPERUSER_USERNAME = admin (optional)
   DJANGO_SUPERUSER_EMAIL = admin@example.com (optional)
   DJANGO_SUPERUSER_PASSWORD = secure-password (optional)
   ```

**Step 3: Configure Deployment**
1. Set up GitHub deployment:
   - App Service → Deployment Center
   - Choose GitHub as source
   - Authorize and select repository
   - Configure build provider (GitHub Actions recommended)

2. Or deploy via Azure CLI:
   ```bash
   az webapp deployment source config --name your-app-name --resource-group myResourceGroup --repo-url https://github.com/yourusername/yourrepo.git --branch main
   ```

**Step 4: Configure Startup Command**
In Azure Portal → App Service → Configuration → General Settings:
```
Startup Command: python startup.py && gunicorn --bind=0.0.0.0 --workers=4 backend.wsgi
```

**Step 5: Database Setup**
1. Create Azure Database for PostgreSQL:
   ```bash
   az postgres server create --resource-group myResourceGroup --name mypostgresserver --admin-user myadmin --admin-password mypassword --sku-name GP_Gen5_2
   ```

2. Create database:
   ```bash
   az postgres db create --resource-group myResourceGroup --server-name mypostgresserver --name mydatabase
   ```

3. Configure firewall to allow Azure services:
   ```bash
   az postgres server firewall-rule create --resource-group myResourceGroup --server mypostgresserver --name AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
   ```

**Step 6: Enable Application Insights (Optional)**
```bash
az monitor app-insights component create --app your-app-name --location eastus --resource-group myResourceGroup
```

### Option 8: VPS/Self-Hosted

**Option A: Using systemd environment file:**
1. Create `/etc/environment` or service-specific env file:
   ```env
   SECRET_KEY=your-secret-key
   DEBUG=False
   METEOMATICS_USERNAME=your-username
   METEOMATICS_PASSWORD=your-password
   ```

**Option B: Export in shell profile:**
```bash
# Add to ~/.bashrc or ~/.profile
export SECRET_KEY="your-secret-key"
export DEBUG=False
export METEOMATICS_USERNAME="your-username"
export METEOMATICS_PASSWORD="your-password"
```

**Option C: Docker with environment file:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    env_file:
      - .env.production
    ports:
      - "8000:8000"
```

---

## 🔐 Security Best Practices

### 1. Never Commit Secrets
- ✅ Use `.env` for local development
- ✅ Use platform environment variables for production
- ❌ Never commit `.env` files to Git
- ❌ Never hardcode secrets in source code

### 2. Secret Management
- **Development**: `.env` file (gitignored)
- **Production**: Platform-specific environment variables
- **CI/CD**: Encrypted secrets in CI/CD platform

### 3. Key Rotation
- Regularly rotate API keys and secrets
- Use different keys for different environments
- Monitor API usage for unauthorized access

---

## 🚀 CI/CD Pipeline

### GitHub Actions Example
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Production
        env:
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
          METEOMATICS_USERNAME: ${{ secrets.METEOMATICS_USERNAME }}
          METEOMATICS_PASSWORD: ${{ secrets.METEOMATICS_PASSWORD }}
        run: |
          # Your deployment commands here
```

**Setting GitHub Secrets:**
1. Repository → Settings → Secrets and Variables → Actions
2. Add each secret individually

---

## 📊 Monitoring & Logging

### Production Logging
The app logs weather API usage to help you monitor:
- Which API (NASA/Meteomatics) is being used
- API failures and fallback triggers
- Performance metrics

### Log Locations
- **Local**: `logs/weather_api.log`
- **Heroku**: `heroku logs --tail`
- **Other platforms**: Check platform-specific logging

---

## 🔧 Troubleshooting

### Common Issues

**1. Environment Variables Not Loading**
```python
# Test in Django shell
import os
print(os.getenv('METEOMATICS_USERNAME'))
```

**2. API Credentials Invalid**
- Test using the built-in endpoint: `/api/weather-sources/test/`
- Check Meteomatics dashboard for API usage/limits

**3. Deployment Issues**
- Ensure `python-dotenv` is in `requirements.txt`
- Check that all required environment variables are set
- Verify `ALLOWED_HOSTS` includes your domain

**4. CORS Issues in Production**
Update CORS settings in `settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
]
```

---

## 📝 Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ | Generated | Django secret key |
| `DEBUG` | ❌ | `True` | Debug mode |
| `ALLOWED_HOSTS` | Production | `localhost,127.0.0.1` | Allowed hosts |
| `METEOMATICS_USERNAME` | ❌ | `None` | Meteomatics API username |
| `METEOMATICS_PASSWORD` | ❌ | `None` | Meteomatics API password |

---

## 🤝 Team Collaboration

### For Team Members
1. **Never share actual credentials in chat/email**
2. **Each developer should have their own Meteomatics account**
3. **Use `.env.example` as a template**
4. **Document any new environment variables**

### Onboarding New Developers
1. Clone the repository
2. Copy `.env.example` to `.env`
3. Get their own Meteomatics credentials (if needed)
4. Run the setup commands

This approach ensures security while making it easy for the team to develop and deploy! 🎉