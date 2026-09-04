import { useState, useCallback } from 'react';
import { APIProvider, Map, Marker, Pin } from '@vis.gl/react-google-maps';

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
const isLocalhost =
  typeof window !== 'undefined' &&
  ['localhost', '127.0.0.1'].includes(window.location.hostname);
const API_BASE =
  import.meta.env.VITE_API_URL || (isLocalhost ? 'http://localhost:8000/api/v1' : '/api/v1');

function toLatLng(e) {
  const ll = e.detail?.latLng;
  if (!ll) return null;
  const lat = typeof ll.lat === 'function' ? ll.lat() : ll.lat;
  const lng = typeof ll.lng === 'function' ? ll.lng() : ll.lng;
  return [lat, lng];
}

/**
 * Reusable LocationPicker component — plan.txt §6.
 *
 * Props:
 *   position    [lat, lng] | null
 *   setPosition ([lat, lng]) => void
 *   address     string
 *   setAddress  (string) => void
 *
 * Features:
 *   - Click map to drop a pin (sets coordinates)
 *   - "Use Current Location" button via Geolocation API
 *   - Address search box + "Mark on Map" button (forward geocoding via Nominatim)
 *   - Automatic reverse geocoding on every pin drop / GPS fix to fill address box
 */
export default function LocationPicker({ position, setPosition, address, setAddress }) {
  const [geoLoading, setGeoLoading] = useState(false);
  const [markLoading, setMarkLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [mapCenter, setMapCenter] = useState(
    position ? { lat: position[0], lng: position[1] } : { lat: 20.5937, lng: 78.9629 }
  );

  // Reverse-geocode helper — calls our own backend endpoint (no key needed)
  const reverseGeocode = useCallback(async (lat, lng) => {
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`${API_BASE}/geocoding/reverse?lat=${lat}&lng=${lng}`, { headers });
      if (res.ok) {
        const data = await res.json();
        if (data.address) setAddress(data.address);
      }
    } catch {
      // Silently fail — user can still type the address manually
    }
  }, [setAddress]);

  // Handle clicking on the map to drop a pin
  const handleMapClick = (e) => {
    const p = toLatLng(e);
    if (!p) return;
    setPosition(p);
    setMapCenter({ lat: p[0], lng: p[1] });
    reverseGeocode(p[0], p[1]);
  };

  // "Use Current Location" button handler
  const handleCurrentLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser.');
      return;
    }
    setGeoLoading(true);
    setError('');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        setPosition([lat, lng]);
        setMapCenter({ lat, lng });
        reverseGeocode(lat, lng);
        setGeoLoading(false);
      },
      () => {
        setError('Could not get your location. Please check browser permissions.');
        setGeoLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  // "Mark on Map" (forward geocode) button handler
  const handleMarkOnMap = async () => {
    const query = searchInput.trim() || address.trim();
    if (!query) {
      setError('Please enter an address to search.');
      return;
    }
    setMarkLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(
        `${API_BASE}/geocoding/search?address=${encodeURIComponent(query)}`,
        { headers }
      );
      if (!res.ok) {
        setError('Address not found. Try a more specific address.');
        return;
      }
      const data = await res.json();
      const lat = data.latitude;
      const lng = data.longitude;
      setPosition([lat, lng]);
      setMapCenter({ lat, lng });
      if (searchInput.trim()) setAddress(searchInput.trim());
    } catch {
      setError('Failed to search address. Please check your connection.');
    } finally {
      setMarkLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      {/* Address input row with "Mark on Map" button */}
      <div>
        <label className="block text-sm font-semibold text-ink mb-1.5">
          Address
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            className="flex-1 px-4 py-2.5 rounded-lg border border-line bg-white text-ink placeholder-ink-muted focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 text-sm"
            placeholder="e.g. Anna Salai, Chennai, Tamil Nadu"
            value={address}
            onChange={(e) => {
              setAddress(e.target.value);
              setSearchInput(e.target.value);
            }}
          />
          <button
            type="button"
            onClick={handleMarkOnMap}
            disabled={markLoading}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition disabled:opacity-60 whitespace-nowrap"
          >
            {markLoading ? (
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a2 2 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            )}
            Place on Map
          </button>
        </div>
      </div>

      {/* "Use Current Location" button */}
      <button
        type="button"
        onClick={handleCurrentLocation}
        disabled={geoLoading}
        className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-primary text-primary bg-primary/5 text-sm font-semibold hover:bg-primary/10 transition disabled:opacity-60 w-full justify-center"
      >
        {geoLoading ? (
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3A8.994 8.994 0 0013 3.06V1h-2v2.06A8.994 8.994 0 003.06 11H1v2h2.06A8.994 8.994 0 0011 20.94V23h2v-2.06A8.994 8.994 0 0020.94 13H23v-2h-2.06z" />
          </svg>
        )}
        {geoLoading ? 'Detecting location…' : '📍 Use My Current Location'}
      </button>

      {error && (
        <p className="text-xs text-red-500 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>
      )}

      {/* Map */}
      <div className="h-72 w-full rounded-card overflow-hidden border border-line shadow-sm">
        <APIProvider apiKey={GOOGLE_MAPS_API_KEY}>
          <Map
            center={mapCenter}
            zoom={position ? 14 : 5}
            style={{ width: '100%', height: '100%' }}
            gestureHandling="greedy"
            onClick={handleMapClick}
          >
            {position && (
              <Marker position={{ lat: position[0], lng: position[1] }}>
                <Pin backgroundColor="#1E5EFF" glyphColor="#fff" borderColor="#0B2545" />
              </Marker>
            )}
          </Map>
        </APIProvider>
      </div>

      <p className="text-xs text-ink-muted">
        Click anywhere on the map to drop a pin, or use the buttons above to set your location.
        {position && (
          <span className="ml-1 font-mono text-ink-muted">
            ({position[0].toFixed(5)}, {position[1].toFixed(5)})
          </span>
        )}
      </p>
    </div>
  );
}
