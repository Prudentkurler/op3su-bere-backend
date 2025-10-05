# Weather Data Configuration Guide

This application uses NASA POWER as the primary weather data source with Meteomatics as a fallback option.

## Configuration

### NASA POWER (Primary)
NASA POWER is used as the primary source and requires no configuration - it's a free public API.

### Meteomatics (Fallback)
Meteomatics requires authentication credentials. To set up the fallback:

1. **Get Meteomatics Credentials**
   - Sign up at https://www.meteomatics.com/
   - Get your username and password from the account dashboard

2. **Configure Credentials**
   
   **For Local Development:**
   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   ```env
   METEOMATICS_USERNAME=your_meteomatics_username
   METEOMATICS_PASSWORD=your_meteomatics_password
   ```
   
   **For Production Deployment:**
   Set environment variables on your hosting platform:
   - Heroku: `heroku config:set METEOMATICS_USERNAME=your_username`
   - Other platforms: Check `DEPLOYMENT.md` for specific instructions

3. **Test Configuration**
   Use the API endpoints to test your configuration:
   ```bash
   # Check weather source status
   curl http://localhost:8000/api/weather-sources/status/
   
   # Test connectivity
   curl -X POST http://localhost:8000/api/weather-sources/test/
   ```

## API Behavior

### Normal Operation
- **Primary**: NASA POWER API is tried first
- **Fallback**: If NASA fails, Meteomatics is used automatically
- **Error**: If both fail, an error is returned

### Data Format
Both APIs return data in the same format for seamless switching:
```python
{
    'T2M': {'20240101': 15.2, '20240102': 16.8, ...},
    'RH2M': {'20240101': 65.0, '20240102': 72.1, ...},
    # ... other parameters
}
```

### Logging
The system logs which data source is used:
- `INFO: Successfully fetched data from NASA POWER`
- `INFO: Successfully fetched data from Meteomatics fallback`

## API Endpoints

### Check Weather Source Status
```
GET /api/weather-sources/status/
```
Returns available weather data sources and their configuration status.

### Test Weather Sources
```
POST /api/weather-sources/test/
```
Tests connectivity to all configured weather data sources.

## Parameter Mapping

| NASA POWER | Meteomatics | Description |
|------------|-------------|-------------|
| T2M | t_2m:C | Daily mean temperature (°C) |
| T2M_MIN | t_min_2m_24h:C | Daily minimum temperature (°C) |
| T2M_MAX | t_max_2m_24h:C | Daily maximum temperature (°C) |
| RH2M | relative_humidity_2m:p | Relative humidity (%) |
| PRECTOTCORR | precip_24h:mm | Daily precipitation (mm) |
| WS10M | wind_speed_10m:ms | Wind speed at 10m (m/s) |

## Troubleshooting

### NASA POWER Issues
- Check internet connectivity
- Verify coordinates are valid (-90 ≤ lat ≤ 90, -180 ≤ lon ≤ 180)
- NASA POWER may have temporary outages

### Meteomatics Issues
- Verify credentials are correct
- Check if your Meteomatics account has sufficient quota
- Ensure credentials are properly configured in environment/settings

### Both APIs Failing
- Check internet connectivity
- Verify firewall settings allow outbound HTTPS connections
- Check logs for detailed error messages

## Cost Considerations

- **NASA POWER**: Free, but may have rate limits
- **Meteomatics**: Paid service, check your subscription limits

## Development

To add more weather data sources:
1. Create a new utility module in `api/utils/`
2. Implement the same interface as NASA/Meteomatics modules
3. Update `weather_data.py` to include the new source
4. Add configuration options as needed