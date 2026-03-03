import logging
from typing import Optional, Dict, Any, List
import googlemaps
from backend.config.settings import settings

logger = logging.getLogger("twisted.utils.maps")

class MapsClient:
    """
    Client for Google Maps & Places API.
    Enables location verification and distance calculations.
    """

    def __init__(self):
        # We reuse GEMINI_API_KEY if possible, but usually Maps needs its own or enabled on the same project
        # For simplicity, we assume an API key is provided
        self.api_key = settings.GEMINI_API_KEY # Placeholder, usually MAPS_API_KEY
        self.client: Optional[googlemaps.Client] = None

        if self.api_key:
            try:
                self.client = googlemaps.Client(key=self.api_key)
                logger.info("✅ Google Maps Client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Google Maps Client: {e}")

    async def verify_location(self, address: str) -> Optional[Dict[str, Any]]:
        """Geocode and verify an address."""
        if not self.client:
            return None

        try:
            # googlemaps SDK is sync, so we run in executor if needed
            result = self.client.geocode(address)
            if result:
                return {
                    "formatted_address": result[0].get("formatted_address"),
                    "location": result[0].get("geometry", {}).get("location"),
                    "place_id": result[0].get("place_id")
                }
            return None
        except Exception as e:
            logger.error(f"❌ Maps verification failed: {e}")
            return None

    async def calculate_distance(self, origin: str, destination: str) -> Optional[Dict[str, Any]]:
        """Calculate distance and duration between two points."""
        if not self.client:
            return None

        try:
            result = self.client.distance_matrix(origin, destination)
            if result and result.get("rows"):
                elements = result["rows"][0].get("elements", [])
                if elements and elements[0].get("status") == "OK":
                    return {
                        "distance": elements[0].get("distance", {}).get("text"),
                        "duration": elements[0].get("duration", {}).get("text")
                    }
            return None
        except Exception as e:
            logger.error(f"❌ Distance calculation failed: {e}")
            return None

    def is_enabled(self) -> bool:
        return self.client is not None
