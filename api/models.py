from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Event(models.Model):
    """Model to store user-defined events and their weather sensitivity"""
    
    # Event details
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=200, help_text="Name of the event (e.g., 'Beach Wedding', 'Mountain Hiking')")
    description = models.TextField(blank=True, help_text="Optional description of the event")
    event_type = models.CharField(max_length=100, help_text="Type/category of event (e.g., 'wedding', 'outdoor_sports')")
    
    # Location and date
    location_name = models.CharField(max_length=200, help_text="Location name (e.g., 'Central Park, NYC')")
    latitude = models.FloatField(validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.FloatField(validators=[MinValueValidator(-180), MaxValueValidator(180)])
    
    # Target date
    target_month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    target_day = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(31)], null=True, blank=True)
    
    # Weather sensitivity (JSON field to store which conditions this event is sensitive to)
    weather_sensitivity = models.JSONField(
        default=list, 
        help_text="List of weather conditions this event is sensitive to (e.g., ['very_hot', 'very_wet'])"
    )
    
    # Analysis results (stored for caching and AI integration)
    last_analysis = models.JSONField(null=True, blank=True, help_text="Last compound extreme analysis results")
    last_analysis_date = models.DateTimeField(null=True, blank=True)
    
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'name']  # Each user can have unique event names
    
    def __str__(self):
        return f"{self.name} ({self.user.email}) - {self.target_month:02d}/{self.target_day or 'XX'}"
    
    def get_target_date_display(self):
        """Get human-readable target date"""
        months = [
            '', 'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        month_name = months[self.target_month]
        if self.target_day:
            return f"{month_name} {self.target_day}"
        return month_name
