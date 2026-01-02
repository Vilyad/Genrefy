from .lastfm_service import LastFMService
from .visualization import VisualizationService

lastfm_service = LastFMService()
visualization_service = VisualizationService()

__all__ = [
    'LastFMService',
    'VisualizationService',
    'lastfm_service',
    'visualization_service'
]