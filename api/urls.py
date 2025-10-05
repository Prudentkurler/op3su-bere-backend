from django.urls import path
from .views import (
    GeocodeView, ReverseGeocodeView, WeatherQueryView, AvailableConditionsView,
    EventListCreateView, EventDetailView, EventAnalysisView, 
    EventDataForAIView, EventSummaryView, WeatherSourceStatusView, WeatherSourceTestView,
    AnalysisSummaryView, GeospatialSegmentationView
)

urlpatterns = [
    # Geocoding endpoints
    path('geocode/', GeocodeView.as_view(), name='geocode'),
    path('reverse-geocode/', ReverseGeocodeView.as_view(), name='reverse_geocode'),
    
    # Weather analysis endpoints
    path('weather/', WeatherQueryView.as_view(), name='weather_query'),
    path('conditions/', AvailableConditionsView.as_view(), name='available_conditions'),
    
    # Weather data source management
    path('weather-sources/status/', WeatherSourceStatusView.as_view(), name='weather_source_status'),
    path('weather-sources/test/', WeatherSourceTestView.as_view(), name='weather_source_test'),
    
    # Event management endpoints
    path('events/', EventListCreateView.as_view(), name='event_list_create'),
    path('events/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    
    # Weather analysis for events
    path('events/analyze/', EventAnalysisView.as_view(), name='event_analysis'),
    
    # Data for AI processing endpoints
    path('events/ai-data/', EventDataForAIView.as_view(), name='event_ai_data'),
    path('events/<int:event_id>/summary/', EventSummaryView.as_view(), name='event_summary'),
    
    # Analysis summary for download
    path('analysis/summary/', AnalysisSummaryView.as_view(), name='analysis_summary'),
    
    # Geospatial segmentation
    path('geospatial-segmentation/', GeospatialSegmentationView.as_view(), name='geospatial_segmentation'),
]
