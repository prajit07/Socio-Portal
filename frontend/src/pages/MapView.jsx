import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import Navbar from '../components/Navbar';
import { problemsApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Card, StatusBadge, Alert, PageLoader } from '../components/ui';

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

function colorIcon(color) {
  return L.divIcon({
    className: '',
    html: `<div style="background:${color};width:16px;height:16px;border-radius:9999px;border:3px solid white;box-shadow:0 0 0 2px ${color};"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

export default function MapView() {
  const { user } = useAuth();
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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
  const center = located[0] ? [located[0].latitude, located[0].longitude] : [20.5937, 78.9629];

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
              <MapContainer center={center} zoom={5} style={{ height: '100%', width: '100%' }}>
                <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                {located.map((p) => (
                  <Marker key={p.id} position={[p.latitude, p.longitude]} icon={colorIcon(STATUS_COLORS[p.status] || '#1E5EFF')}>
                    <Popup>
                      <div className="space-y-1">
                        <div className="font-bold">{p.title}</div>
                        <StatusBadge status={p.status} size="sm" />
                        <Link to={`/problems/${p.id}`} className="text-primary text-xs font-semibold">View details</Link>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          </Card>
        )}
      </main>
    </div>
  );
}
