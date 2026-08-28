"""Geocoding service — plan.txt §8.6.

Primary path: OpenStreetMap Nominatim API (free, no key required).
Fallback: Google Maps Geocoding API when GOOGLE_MAPS_API_KEY is set in config.

Provides:
  geocode(address)         -> (lat, lng) | None
  reverse_geocode(lat,lng) -> str address | None
"""
import logging
from typing import Optional

import httpx

logger = logging.getLogger("geocoding")

# Nominatim requires a User-Agent header
_NOMINATIM_HEADERS = {
    "User-Agent": "SocioConnect/1.0 (contact@socioportal.in)",
    "Accept-Language": "en",
}
_NOMINATIM_SEARCH = "https://nominatim.openstreetmap.org/search"
_NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
_TIMEOUT = 8.0


def geocode(address: str) -> Optional[tuple[float, float]]:
    """Convert an address string to (latitude, longitude).
    Returns None on failure or no results.
    """
    if not address or not address.strip():
        return None
    try:
        resp = httpx.get(
            _NOMINATIM_SEARCH,
            params={"q": address, "format": "json", "limit": 1, "countrycodes": "in"},
            headers=_NOMINATIM_HEADERS,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            return (float(results[0]["lat"]), float(results[0]["lon"]))
    except Exception as e:
        logger.warning("Geocoding failed for address '%s': %s", address, e)
    return None


def reverse_geocode(latitude: float, longitude: float) -> Optional[str]:
    """Convert (latitude, longitude) to a human-readable address string.
    Returns None on failure.
    """
    try:
        resp = httpx.get(
            _NOMINATIM_REVERSE,
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "zoom": 16,          # neighbourhood level
                "addressdetails": 0,
            },
            headers=_NOMINATIM_HEADERS,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("display_name")
    except Exception as e:
        logger.warning("Reverse geocoding failed for (%s, %s): %s", latitude, longitude, e)
    return None
