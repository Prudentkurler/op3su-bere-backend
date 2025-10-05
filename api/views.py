from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Event
from .serializers import EventSerializer, EventAnalysisSerializer
from .utils.nominatim import geocode, reverse_geocode
from .utils.weather_data import fetch_historical_data_for_date, get_available_weather_sources, test_weather_sources
from .utils.compound_extremes import calculate_probability, CONDITIONS, EVENT_TYPES

class GeocodeView(APIView):
    def post(self, request):
        q = request.data.get('q')
        if not q:
            return Response({'error': 'q required'}, status=status.HTTP_400_BAD_REQUEST)
        res = geocode(q)
        if not res:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(res)

class ReverseGeocodeView(APIView):
    def post(self, request):
        lat = request.data.get('lat')
        lon = request.data.get('lon')
        if lat is None or lon is None:
            return Response({'error': 'lat and lon required'}, status=status.HTTP_400_BAD_REQUEST)
        display = reverse_geocode(lat, lon)
        return Response({'display_name': display})

class WeatherQueryView(APIView):
    def post(self, request):
        """
        Enhanced weather query endpoint that handles:
        - location: place name
        - month: target month (1-12)
        - day: target day (1-31, required)
        - condition: weather condition to analyze
        - event_type: type of event (optional)
        """
        location = request.data.get('location')
        month = request.data.get('month')
        day = request.data.get('day')  # Required specific day
        condition = request.data.get('condition')
        event_type = request.data.get('event_type')  # Optional event type

        # Validate required fields
        if not location or not month or not day or not condition:
            return Response({
                'error': 'location, month, day, and condition are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate condition
        if condition not in CONDITIONS:
            available_conditions = list(CONDITIONS.keys())
            return Response({
                'error': f'Invalid condition. Available: {available_conditions}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Note: event_type is optional and can be any custom string

        # Resolve month if needed
        try:
            if isinstance(month, str):
                month = datetime.strptime(month, '%B').month
            else:
                month = int(month)
        except Exception:
            return Response({'error': 'invalid month format'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate day (required)
        try:
            day = int(day)
            if not (1 <= day <= 31):
                return Response({'error': 'day must be between 1 and 31'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'invalid day format'}, status=status.HTTP_400_BAD_REQUEST)

        # Geocode the place using Nominatim
        coords = geocode(location)
        if not coords:
            return Response({'error': 'location not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Fetch weather data using fallback mechanism
            from .utils.weather_data import fetch_weather_data_with_fallback
            power_data, data_source = fetch_weather_data_with_fallback(
                coords['lat'], 
                coords['lon'], 
                month, 
                day, 
                years_back=25
            )

            # Run compound extremes analysis
            result = calculate_probability(
                power_data, 
                month, 
                day, 
                condition, 
                event_type
            )

            # Add location information to result
            result['location'] = {
                'name': location,
                'coordinates': coords,
                'display_name': coords.get('display_name')
            }

            # Add metadata including actual data source used
            result['analysis_metadata'] = {
                'data_source': data_source.upper(),
                'analysis_period': '25 years',
                'target_date': f"{month:02d}/{day:02d}",
                'timestamp': datetime.now().isoformat(),
                'fallback_used': data_source != 'nasa'
            }

            return Response(result)

        except Exception as e:
            return Response({
                'error': f'Failed to analyze weather data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AvailableConditionsView(APIView):
    """Endpoint to get available weather conditions and event types"""
    def get(self, request):
        return Response({
            'weather_conditions': {
                key: {
                    'display_name': value['display_name'],
                    'description': value['description'],
                    'variables': value['variables'],
                    'thresholds': value['thresholds'],
                    'logic': value['logic']
                }
                for key, value in CONDITIONS.items()
            },
            'event_types': {
                key: {
                    'description': value['description'],
                    'sensitive_to': value['sensitive_to']
                }
                for key, value in EVENT_TYPES.items()
            }
        })


# Event Management Views
class EventListCreateView(generics.ListCreateAPIView):
    """List user's events or create a new event"""
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Event.objects.filter(user=self.request.user)


class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific event"""
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Event.objects.filter(user=self.request.user)


class EventAnalysisView(APIView):
    """Run weather analysis for a specific event"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = EventAnalysisSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        event_id = serializer.validated_data['event_id']
        conditions = serializer.validated_data.get('conditions')
        force_refresh = serializer.validated_data.get('force_refresh', False)
        
        # Get the event (ensure it belongs to the user)
        try:
            event = Event.objects.get(id=event_id, user=request.user)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Use event's weather sensitivity if conditions not provided
        if not conditions:
            conditions = event.weather_sensitivity
            if not conditions:
                return Response({
                    'error': 'No conditions specified and event has no weather sensitivity set'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if we need to refresh or can use cached results
        if not force_refresh and event.last_analysis and event.last_analysis_date:
            # Use cached results if less than 24 hours old
            time_diff = timezone.now() - event.last_analysis_date
            if time_diff < timedelta(hours=24):
                return Response({
                    'event': EventSerializer(event).data,
                    'analysis_results': event.last_analysis,
                    'cached': True,
                    'last_updated': event.last_analysis_date
                })
        
        try:
            # Run the compound extremes analysis using fallback mechanism
            from .utils.weather_data import fetch_weather_data_with_fallback
            power_data, data_source = fetch_weather_data_with_fallback(
                event.latitude, 
                event.longitude, 
                event.target_month, 
                event.target_day, 
                years_back=25
            )
            
            # Analyze all specified conditions
            analysis_results = {}
            for condition in conditions:
                if condition in CONDITIONS:
                    result = calculate_probability(
                        power_data,
                        event.target_month,
                        event.target_day,
                        condition,
                        event_type=event.event_type  # Use dynamic event type
                    )
                    analysis_results[condition] = result
            
            # Store the analysis results in the event
            event.last_analysis = analysis_results
            event.last_analysis_date = timezone.now()
            event.save()
            
            return Response({
                'event': EventSerializer(event).data,
                'analysis_results': analysis_results,
                'cached': False,
                'last_updated': event.last_analysis_date,
                'data_source': data_source.upper(),
                'fallback_used': data_source != 'nasa'
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to analyze weather data: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EventDataForAIView(APIView):
    """Provide event data and analysis results for frontend AI processing"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from .serializers import EventDataForAISerializer
        
        serializer = EventDataForAISerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        event_id = serializer.validated_data['event_id']
        include_analysis = serializer.validated_data.get('include_analysis', True)
        
        # Get the event
        try:
            event = Event.objects.get(id=event_id, user=request.user)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Prepare event data for AI processing
        event_data = {
            'id': event.id,
            'name': event.name,
            'event_type': event.event_type,
            'description': event.description,
            'location': {
                'name': event.location_name,
                'latitude': event.latitude,
                'longitude': event.longitude
            },
            'date': {
                'month': event.target_month,
                'day': event.target_day,
                'display': event.get_target_date_display()
            },
            'weather_sensitivity': event.weather_sensitivity,
            'created_at': event.created_at,
            'updated_at': event.updated_at
        }
        
        response_data = {
            'event': event_data
        }
        
        # Include analysis data if requested and available
        if include_analysis:
            if event.last_analysis:
                response_data['analysis'] = {
                    'results': event.last_analysis,
                    'last_updated': event.last_analysis_date,
                    'conditions_analyzed': list(event.last_analysis.keys()) if isinstance(event.last_analysis, dict) else []
                }
            else:
                response_data['analysis'] = {
                    'results': None,
                    'message': 'No weather analysis available. Run analysis first.'
                }
        
        # Add available weather conditions for reference
        response_data['available_conditions'] = {
            condition: {
                'description': details['description'],
                'variables': details['variables']
            }
            for condition, details in CONDITIONS.items()
        }
        
        return Response(response_data)


class EventSummaryView(APIView):
    """Get comprehensive event summary with analysis for AI processing"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id, user=request.user)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get detailed event information
        event_summary = {
            'event': EventSerializer(event).data,
            'analysis_available': bool(event.last_analysis),
            'analysis_results': event.last_analysis,
            'analysis_date': event.last_analysis_date
        }
        
        # Add weather context for AI
        if event.last_analysis:
            weather_context = []
            for condition, results in event.last_analysis.items():
                weather_context.append({
                    'condition': condition,
                    'description': results.get('condition_description', ''),
                    'probability': results.get('probability', 0),
                    'risk_level': self._get_risk_level(results.get('probability', 0))
                })
            event_summary['weather_context'] = weather_context
        
        return Response(event_summary)
    
    def _get_risk_level(self, probability):
        """Convert probability to risk level for AI context"""
        if probability > 75:
            return 'HIGH'
        elif probability > 50:
            return 'MODERATE'
        elif probability > 25:
            return 'LOW_MODERATE'
        else:
            return 'LOW'


class WeatherSourceStatusView(APIView):
    """Get status of available weather data sources"""
    def get(self, request):
        sources = get_available_weather_sources()
        return Response({
            'sources': sources,
            'primary': 'nasa',
            'fallback': 'meteomatics' if sources['meteomatics']['available'] else None
        })


class WeatherSourceTestView(APIView):
    """Test connectivity to weather data sources"""
    def post(self, request):
        test_results = test_weather_sources()
        
        # Determine overall status
        nasa_ok = test_results.get('nasa', {}).get('status') == 'success'
        meteomatics_ok = test_results.get('meteomatics', {}).get('status') == 'success'
        
        overall_status = 'healthy' if nasa_ok else ('degraded' if meteomatics_ok else 'unhealthy')
        
        return Response({
            'overall_status': overall_status,
            'test_results': test_results,
            'recommendations': self._get_recommendations(nasa_ok, meteomatics_ok)
        })
    
    def _get_recommendations(self, nasa_ok, meteomatics_ok):
        """Provide recommendations based on API status"""
        if nasa_ok and meteomatics_ok:
            return ['All weather data sources are working properly']
        elif nasa_ok and not meteomatics_ok:
            return [
                'Primary NASA POWER API is working',
                'Configure Meteomatics credentials for redundancy'
            ]
        elif not nasa_ok and meteomatics_ok:
            return [
                'NASA POWER API is down, using Meteomatics fallback',
                'Check NASA POWER API status'
            ]
        else:
            return [
                'Both weather APIs are unavailable',
                'Check internet connectivity and API credentials',
                'Weather analysis may not work until APIs are restored'
            ]


class GeospatialSegmentationView(APIView):
    """Geospatial segmentation API for finding locations with similar weather conditions"""
    
    def post(self, request):
        """
        Perform geospatial weather analysis around a center location
        
        Expected input:
        - location: string location name (e.g., "Accra")
        - month: integer (1-12) or month name
        - condition: weather condition key ("very_hot", "very_cold", "very_wet", "very_windy") 
        - step: optional float, degree increment for grid (default: 0.5)
        - range: optional float, how far to explore in degrees (default: 1.0)
        """
        # Extract and validate input parameters
        location = request.data.get('location')
        month = request.data.get('month')
        condition = request.data.get('condition')
        step = float(request.data.get('step', 0.5))
        search_range = float(request.data.get('range', 1.0))
        
        # Validate required parameters
        if not location or not month or not condition:
            return Response({
                'error': 'location, month, and condition are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate condition
        if condition not in CONDITIONS:
            available_conditions = list(CONDITIONS.keys())
            return Response({
                'error': f'Invalid condition. Available: {available_conditions}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate and convert month
        try:
            if isinstance(month, str):
                month = datetime.strptime(month, '%B').month
            else:
                month = int(month)
            if not (1 <= month <= 12):
                raise ValueError("Month must be between 1 and 12")
        except Exception:
            return Response({
                'error': 'Invalid month format. Use 1-12 or month name like "January"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate step and range parameters
        if step <= 0 or step > 5:
            return Response({
                'error': 'Step must be between 0 and 5 degrees'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if search_range <= 0 or search_range > 10:
            return Response({
                'error': 'Range must be between 0 and 10 degrees'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Geocode the center location
            center_coords = geocode(location)
            if not center_coords:
                return Response({
                    'error': f'Location "{location}" not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            center_lat = center_coords['lat']
            center_lon = center_coords['lon']
            center_display_name = center_coords.get('display_name', location)
            
            # Generate grid of coordinate points
            coordinate_grid = self._generate_coordinate_grid(
                center_lat, center_lon, search_range, step
            )
            
            # Perform weather analysis for each point
            results = []
            failed_points = 0
            
            for lat, lon in coordinate_grid:
                try:
                    # Get weather data for this coordinate
                    from .utils.weather_data import fetch_weather_data_with_fallback
                    power_data, data_source = fetch_weather_data_with_fallback(
                        lat, lon, month, years_back=25
                    )
                    
                    # Perform compound extreme analysis
                    analysis_result = calculate_probability(
                        power_data, month, None, condition, None
                    )
                    
                    # Get location name for this coordinate
                    location_name = reverse_geocode(lat, lon)
                    
                    # Format result
                    point_result = {
                        'lat': round(lat, 4),
                        'lon': round(lon, 4), 
                        'location': location_name or f"({lat:.2f}, {lon:.2f})",
                        'probability': analysis_result.get('probability', 0),
                        'weather_condition': condition,
                        'variables': analysis_result.get('variables_analyzed', []),
                        'years_total': analysis_result.get('years_total', 0),
                        'years_matching': analysis_result.get('years_matching', 0),
                        'data_source': data_source.upper()
                    }
                    
                    results.append(point_result)
                    
                except Exception as point_error:
                    failed_points += 1
                    # Log the error but continue with other points
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to analyze point ({lat}, {lon}): {str(point_error)}")
                    continue
            
            # Sort results by probability (highest first)
            results.sort(key=lambda x: x['probability'], reverse=True)
            
            # Prepare response
            response_data = {
                'center_location': center_display_name,
                'center_coordinates': {
                    'lat': center_lat,
                    'lon': center_lon
                },
                'condition': condition,
                'condition_description': CONDITIONS[condition]['description'],
                'month': month,
                'range': search_range,
                'step': step,
                'total_points_analyzed': len(coordinate_grid),
                'successful_analyses': len(results),
                'failed_analyses': failed_points,
                'results': results
            }
            
            return Response(response_data)
            
        except Exception as e:
            return Response({
                'error': f'Geospatial analysis failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_coordinate_grid(self, center_lat, center_lon, search_range, step):
        """
        Generate a grid of coordinate points around the center location
        
        Args:
            center_lat (float): Center latitude
            center_lon (float): Center longitude  
            search_range (float): Distance to search in degrees
            step (float): Step size in degrees
            
        Returns:
            list: List of (lat, lon) tuples
        """
        coordinates = []
        
        # Calculate the number of steps in each direction
        steps = int(search_range / step)
        
        # Generate grid points
        for lat_step in range(-steps, steps + 1):
            for lon_step in range(-steps, steps + 1):
                lat = center_lat + (lat_step * step)
                lon = center_lon + (lon_step * step)
                
                # Basic bounds checking (rough earth bounds)
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    coordinates.append((lat, lon))
        
        return coordinates


class AnalysisSummaryView(APIView):
    """Get comprehensive analysis summary for download"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Generate downloadable summary from analysis data.
        Expects the same data structure that's stored in localStorage on frontend.
        """
        # Get analysis data from request body (sent from frontend)
        analysis_data = request.data.get('analysis_data')
        
        if not analysis_data:
            return Response({
                'error': 'analysis_data is required in request body'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Process and format the summary data
            summary = self._format_analysis_summary(analysis_data)
            return Response({
                'summary': summary,
                'timestamp': datetime.now().isoformat(),
                'user': request.user.username
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to generate summary: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _format_analysis_summary(self, data):
        """Format analysis data into a structured summary"""
        # Extract basic information
        location = data.get('location', {})
        probability = data.get('probability', 0)
        condition_description = data.get('condition_description', 'Unknown condition')
        event_type = data.get('event_type', 'Not specified')
        variables_analyzed = data.get('variables_analyzed', [])
        thresholds = data.get('thresholds', {})
        years_total = data.get('years_total', 0)
        years_matching = data.get('years_matching', 0)
        matching_years = data.get('matching_years', [])
        analysis_metadata = data.get('analysis_metadata', {})
        
        # Determine weather condition category
        weather_condition = self._categorize_condition(condition_description, variables_analyzed)
        
        # Create formatted summary
        summary = {
            # Basic Information
            'analysis_id': f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'date_generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            
            # Location Information
            'location': {
                'name': location.get('name', 'Unknown'),
                'coordinates': {
                    'latitude': location.get('coordinates', {}).get('lat', 0),
                    'longitude': location.get('coordinates', {}).get('lon', 0)
                },
                'display_name': location.get('display_name', location.get('name', 'Unknown'))
            },
            
            # Weather Condition
            'weather_condition': {
                'category': weather_condition,
                'description': condition_description,
                'probability_percent': probability
            },
            
            # Variables and Analysis
            'variables_analyzed': [
                {
                    'variable': var,
                    'threshold': thresholds.get(var, 'Not specified'),
                    'unit': self._get_variable_unit(var)
                }
                for var in variables_analyzed
            ],
            
            # Compound Extreme Analysis Results
            'analysis_results': {
                'total_years_analyzed': years_total,
                'matching_years_count': years_matching,
                'probability_percentage': probability,
                'risk_level': self._get_risk_level(probability),
                'matching_years': matching_years,
                'confidence_level': self._get_confidence_level(years_total)
            },
            
            # Event Information
            'event_details': {
                'event_type': event_type,
                'target_date': analysis_metadata.get('target_date', 'Not specified')
            },
            
            # Technical Metadata
            'metadata': {
                'data_source': analysis_metadata.get('data_source', 'Unknown'),
                'analysis_period': analysis_metadata.get('analysis_period', 'Unknown'),
                'timestamp': analysis_metadata.get('timestamp', datetime.now().isoformat()),
                'fallback_used': analysis_metadata.get('fallback_used', False)
            }
        }
        
        return summary
    
    def _categorize_condition(self, description, variables):
        """Categorize the weather condition based on description and variables"""
        description_lower = description.lower()
        
        if 'hot' in description_lower or 'temperature' in description_lower:
            if any('hot' in var.lower() for var in variables):
                return 'very_hot'
            return 'temperature_related'
        elif 'cold' in description_lower:
            return 'very_cold'
        elif 'wet' in description_lower or 'rain' in description_lower or 'precipitation' in description_lower:
            return 'very_wet'
        elif 'dry' in description_lower:
            return 'very_dry'
        elif 'wind' in description_lower:
            return 'windy'
        else:
            return 'other'
    
    def _get_variable_unit(self, variable):
        """Get the unit for a weather variable"""
        unit_map = {
            'T2M': '°C',
            'T2M_MAX': '°C',
            'T2M_MIN': '°C',
            'PRECTOT': 'mm/day',
            'PRECTOTCORR': 'mm/day',
            'WS2M': 'm/s',
            'WS10M': 'm/s',
            'RH2M': '%',
            'PS': 'kPa',
            'QV2M': 'g/kg'
        }
        return unit_map.get(variable, 'unknown')
    
    def _get_risk_level(self, probability):
        """Convert probability to risk level"""
        if probability >= 80:
            return 'Very High'
        elif probability >= 60:
            return 'High'
        elif probability >= 40:
            return 'Moderate'
        elif probability >= 20:
            return 'Low'
        else:
            return 'Very Low'
    
    def _get_confidence_level(self, years_analyzed):
        """Determine confidence level based on years of data"""
        if years_analyzed >= 25:
            return 'High'
        elif years_analyzed >= 15:
            return 'Moderate'
        elif years_analyzed >= 10:
            return 'Low'
        else:
            return 'Very Low'
