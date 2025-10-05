from rest_framework import serializers
from .models import Event
from .utils.nominatim import geocode
from .utils.compound_extremes import CONDITIONS


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event model with location geocoding"""
    
    # Read-only fields for display
    target_date_display = serializers.CharField(source='get_target_date_display', read_only=True)
    location_coordinates = serializers.SerializerMethodField()
    
    # Optional fields for creating events without providing coordinates
    location_only = serializers.CharField(write_only=True, required=False, 
                                         help_text="Provide only location name, coordinates will be geocoded automatically")
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'description', 'event_type', 'location_name', 
            'latitude', 'longitude', 'location_coordinates', 'location_only',
            'target_month', 'target_day', 'target_date_display',
            'weather_sensitivity', 'last_analysis', 'last_analysis_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['last_analysis', 'last_analysis_date']
        extra_kwargs = {
            'location_name': {'required': False},
            'latitude': {'required': False},
            'longitude': {'required': False},
        }
    
    def get_location_coordinates(self, obj):
        """Return formatted coordinates"""
        return {
            'latitude': obj.latitude,
            'longitude': obj.longitude
        }
    
    def validate_weather_sensitivity(self, value):
        """Validate that weather sensitivity contains valid condition keys"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Weather sensitivity must be a list")
        
        valid_conditions = set(CONDITIONS.keys())
        invalid_conditions = set(value) - valid_conditions
        
        if invalid_conditions:
            raise serializers.ValidationError(
                f"Invalid weather conditions: {list(invalid_conditions)}. "
                f"Valid options: {list(valid_conditions)}"
            )
        
        return value
    
    def validate(self, data):
        """Custom validation for the entire serializer"""
        # Handle location geocoding
        location_only = data.pop('location_only', None)
        has_location_only = location_only is not None
        
        if location_only:
            # Geocode the location
            coords = geocode(location_only)
            if not coords:
                raise serializers.ValidationError({
                    'location_only': f"Could not geocode location: {location_only}"
                })
            
            data['location_name'] = location_only
            data['latitude'] = coords['lat']
            data['longitude'] = coords['lon']
        
        # Validate that either coordinates are provided or location_only was used
        if not all([data.get('latitude'), data.get('longitude'), data.get('location_name')]):
            if not has_location_only:
                raise serializers.ValidationError(
                    "Either provide latitude/longitude/location_name or use location_only field"
                )
        
        # Validate target date
        target_month = data.get('target_month')
        target_day = data.get('target_day')
        
        if target_day and target_month:
            # Basic validation for days in month (simplified)
            days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # Leap year friendly
            if target_day > days_in_month[target_month - 1]:
                raise serializers.ValidationError({
                    'target_day': f"Invalid day {target_day} for month {target_month}"
                })
        
        return data
    
    def create(self, validated_data):
        """Create event and assign to current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class EventAnalysisSerializer(serializers.Serializer):
    """Serializer for requesting weather analysis for an event"""
    
    event_id = serializers.IntegerField()
    conditions = serializers.ListField(
        child=serializers.ChoiceField(choices=list(CONDITIONS.keys())),
        required=False,
        help_text="List of conditions to analyze. If not provided, uses event's weather_sensitivity"
    )
    force_refresh = serializers.BooleanField(
        default=False,
        help_text="Force refresh analysis even if recent data exists"
    )


class EventDataForAISerializer(serializers.Serializer):
    """Serializer for providing event data to frontend for AI processing"""
    
    event_id = serializers.IntegerField()
    include_analysis = serializers.BooleanField(
        default=True,
        help_text="Include weather analysis data in the response"
    )
