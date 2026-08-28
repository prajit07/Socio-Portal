import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { APIProvider, Map, Marker, Pin, InfoWindow } from '@vis.gl/react-google-maps';
import Navbar from '../components/Navbar';
import { problemsApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Card, StatusBadge, Alert, Badge } from '../components/ui';

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

const STATUS_COLORS = {
  pending_validation: '#8A94A6',
  validated: '#1E5EFF',
  open: '#1E5EFF',
  in_review: '#0B2545',
  proposal_submitted: '#0B2545',
  in_collaboration: '#22C7F2',
  prototype: '#22C7F2',
  pilot: '#1B9C68',
  implemented: '#1B9C68',
  closed: '#8A94A6',
  duplicate: '#D64550',
  rejected: '#D64550',
};

export default function MapView() {
  const { user } = useAuth();
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [active, setActive] = useState(null);

  useEffect(() => { load(); }, []);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await problemsApi.list({ limit: 500 });
      // Safely handle both array and paginated-object responses
      const data = Array.isArray(res.data)
        ? res.data
        : res.data?.items ?? res.data?.results ?? [];
      setProblems(data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load map data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const located = problems.filter(
    (p) => typeof p.latitude === 'number' && typeof p.longitude === 'number'
  );
  const center = located.length > 0
    ? { lat: located[0].latitude, lng: located[0].longitude }
    : { lat: 20.5937, lng: 78.9629 };

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h1 className="text-2xl font-extrabold text-primary-navy">Problem Map</h1>
            <p className="text-ink-soft mt-1">
              {loading
                ? 'Loading problems…'
                : `${located.length} of ${problems.length} problems have location data.`}
            </p>
          </div>
          <div className="flex gap-2 flex-wrap">
            {/* Status legend */}
            {!loading && located.length > 0 && (
              <>
                {['open', 'in_review', 'in_collaboration', 'implemented'].map((s) => (
                  <Badge key={s} variant="outline" className="gap-1 text-xs">
                    <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: STATUS_COLORS[s] }} />
                    {s.replace(/_/g, ' ')}
                  </Badge>
                ))}
              </>
            )}
          </div>
        </div>

        {error && (
          <Alert variant="danger" className="mb-4">
            {error}
            <button onClick={load} className="ml-2 underline font-semibold">Retry</button>
          </Alert>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center h-[70vh] gap-4">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            <p className="text-ink-muted text-sm">Loading map data…</p>
          </div>
        ) : (
          <Card padding="none" className="overflow-hidden">
            <div className="h-[70vh] w-full">
              <APIProvider apiKey={GOOGLE_MAPS_API_KEY}>
                <Map
                  defaultCenter={center}
                  defaultZoom={located.length > 0 ? 6 : 5}
                  style={{ width: '100%', height: '100%' }}
                  gestureHandling="greedy"
                >
                  {located.map((p) => (
                    <Marker
                      key={p.id}
                      position={{ lat: p.latitude, lng: p.longitude }}
                      onClick={() => setActive(p)}
                    >
                      <Pin backgroundColor={STATUS_COLORS[p.status] || '#1E5EFF'} glyphColor="#fff" borderColor="#0B2545" />
                    </Marker>
                  ))}
                  {active && (
                    <InfoWindow
                      position={{ lat: active.latitude, lng: active.longitude }}
                      onCloseClick={() => setActive(null)}
                    >
                      <div className="space-y-1 min-w-[180px]">
                        <div className="font-bold text-sm">{active.title}</div>
                        <StatusBadge status={active.status} size="sm" />
                        {active.address && (
                          <p className="text-xs text-gray-500 mt-1">{active.address}</p>
                        )}
                        {active.ai_category && (
                          <p className="text-xs text-gray-400">{active.ai_category}</p>
                        )}
                        <Link
                          to={`/problems/${active.id}`}
                          className="text-primary text-xs font-semibold block mt-2 hover:underline"
                        >
                          View details →
                        </Link>
                      </div>
                    </InfoWindow>
                  )}
                </Map>
              </APIProvider>
            </div>
          </Card>
        )}

        {!loading && located.length === 0 && !error && (
          <div className="mt-6 text-center py-12 text-ink-muted">
            <p className="text-4xl mb-3">📍</p>
            <p className="font-semibold">No problems with location data yet.</p>
            <p className="text-sm mt-1">Problems submitted with a pin or "Use My Current Location" will appear here.</p>
          </div>
        )}

        {/* Summary stats */}
        {!loading && (
          <div className="mt-6 grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="text-center py-4">
              <div className="text-2xl font-extrabold text-primary-navy">{problems.length}</div>
              <div className="text-xs text-ink-muted mt-1">Total Problems</div>
            </Card>
            <Card className="text-center py-4">
              <div className="text-2xl font-extrabold text-primary-navy">{located.length}</div>
              <div className="text-xs text-ink-muted mt-1">Located on Map</div>
            </Card>
            <Card className="text-center py-4">
              <div className="text-2xl font-extrabold text-tag-success">
                {problems.filter((p) => ['implemented', 'closed'].includes(p.status)).length}
              </div>
              <div className="text-xs text-ink-muted mt-1">Resolved</div>
            </Card>
            <Card className="text-center py-4">
              <div className="text-2xl font-extrabold text-primary">
                {problems.filter((p) => ['open', 'validated', 'in_review'].includes(p.status)).length}
              </div>
              <div className="text-xs text-ink-muted mt-1">Active / Open</div>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}
