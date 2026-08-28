import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { APIProvider, Map, Marker, Pin, InfoWindow } from '@vis.gl/react-google-maps';
import Navbar from '../components/Navbar';
import { problemsApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Card, StatusBadge, Alert, PageLoader } from '../components/ui';

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
    try {
      const res = await problemsApi.list({ limit: 200 });
      setProblems(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load map.');
    } finally {
      setLoading(false);
    }
  };

  const located = problems.filter((p) => p.latitude && p.longitude);
  const center = located[0] ? { lat: located[0].latitude, lng: located[0].longitude } : { lat: 20.5937, lng: 78.9629 };

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-extrabold text-primary-navy">Problem Map</h1>
          <p className="text-ink-soft mt-1">{located.length} problems with location data.</p>
        </div>
        {error && <Alert variant="danger" className="mb-4">{error}</Alert>}
        {loading ? <PageLoader /> : (
          <Card padding="none" className="overflow-hidden">
            <div className="h-[70vh] w-full">
              <APIProvider apiKey={GOOGLE_MAPS_API_KEY}>
                <Map
                  defaultCenter={center}
                  defaultZoom={5}
                  style={{ width: '100%', height: '100%' }}
                  gestureHandling="greedy"
                >
                  {located.map((p) => (
                    <Marker
                      key={p.id}
                      position={{ lat: p.latitude, lng: p.longitude }}
                      onClick={() => setActive(p)}
                    >
                      <Pin backgroundColor={STATUS_COLORS[p.status] || '#1E5EFF'} />
                    </Marker>
                  ))}
                  {active && (
                    <InfoWindow
                      position={{ lat: active.latitude, lng: active.longitude }}
                      onCloseClick={() => setActive(null)}
                    >
                      <div className="space-y-1">
                        <div className="font-bold">{active.title}</div>
                        <StatusBadge status={active.status} size="sm" />
                        <Link to={`/problems/${active.id}`} className="text-primary text-xs font-semibold">View details</Link>
                      </div>
                    </InfoWindow>
                  )}
                </Map>
              </APIProvider>
            </div>
          </Card>
        )}
      </main>
    </div>
  );
}
