"""Geocoding API endpoints — plan.txt §8.6.

GET /api/v1/geocoding/search?address=<str>
    -> { latitude, longitude, display_name }

GET /api/v1/geocoding/reverse?lat=<float>&lng=<float>
    -> { address }
"""
from fastapi import APIRouter, HTTPException, Query

from app.services.geocoding_service import geocode, reverse_geocode

router = APIRouter(prefix="/geocoding", tags=["geocoding"])


@router.get("/search")
def search_address(address: str = Query(..., min_length=2, description="Address or place name to geocode")):
    """Convert an address to lat/lng coordinates using OpenStreetMap Nominatim."""
    result = geocode(address)
    if result is None:
        raise HTTPException(status_code=404, detail="Address not found. Try a more specific query.")
    lat, lng = result
    return {"latitude": lat, "longitude": lng, "query": address}


@router.get("/reverse")
def reverse_address(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    """Convert lat/lng coordinates to a human-readable address using OpenStreetMap Nominatim."""
    address = reverse_geocode(lat, lng)
    if address is None:
        raise HTTPException(status_code=404, detail="No address found for these coordinates.")
    return {"address": address, "latitude": lat, "longitude": lng}
