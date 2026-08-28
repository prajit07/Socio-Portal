import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { APIProvider, Map, Marker, Pin, InfoWindow } from '@vis.gl/react-google-maps';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import { Card, Button, StatusBadge, Alert, PageLoader, Badge, Input, Select } from '../components/ui';

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

const STATUS_COLORS = {
  pending_validation: '#8A94A6', validated: '#1E5EFF', open: '#1E5EFF',
  in_review: '#0B2545', proposal_submitted: '#0B2545', in_collaboration: '#22C7F2',
  prototype: '#22C7F2', pilot: '#1B9C68', implemented: '#1B9C68', closed: '#8A94A6',
  duplicate: '#D64550', rejected: '#D64550',
};

const CATEGORIES = [
  'Water & Sanitation', 'Waste Management', 'Health & Healthcare', 'Education',
  'Transportation & Mobility', 'Energy & Environment', 'Agriculture & Rural',
  'Housing & Urban Development', 'Digital Governance', 'Livelihood & Employment',
  'Disaster Management', 'Public Safety & Security',
];

export default function PublicMap() {
  const { user } = useAuth();
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [active, setActive] = useState(null);
  const [filterCategory, setFilterCategory] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Location Filter State
  const [userLocation, setUserLocation] = useState(null); // { lat, lng }
  const [radiusKm, setRadiusKm] = useState(10);
  const [fetchingLocation, setFetchingLocation] = useState(false);

  useEffect(() => { load(); }, []);

  const load = async () => {
    setLoading(true);
    try {
      // Try fetching as authenticated; fall back to empty on 401
      const res = await api.get('/problems', { params: { limit: 500 } }).catch(() => null);
      const data = Array.isArray(res?.data)
        ? res.data
        : res?.data?.items ?? res?.data?.results ?? [];
      setProblems(data);
    } catch {
      // Silently handle — public map can work with no data
    } finally {
      setLoading(false);
    }
  };

  // Only keep problems where lat/lng are actual numbers
  const located = problems.filter(
    (p) => typeof p.latitude === 'number' && typeof p.longitude === 'number'
  );
  // Haversine formula to calculate distance in km
  const getDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; // Radius of the earth in km
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  const handleFetchLocation = () => {
    setFetchingLocation(true);
    setError('');
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser.');
      setFetchingLocation(false);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
        setFetchingLocation(false);
      },
      (err) => {
        console.warn('Geolocation error:', err);
        setError('Unable to fetch your location. Please check your browser permissions.');
        setFetchingLocation(false);
      }
    );
  };

  const filtered = located.filter((p) => {
    if (filterCategory && p.ai_category !== filterCategory) return false;
    if (filterStatus && p.status !== filterStatus) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      if (!p.title?.toLowerCase().includes(q) && !p.description?.toLowerCase().includes(q) && !p.address?.toLowerCase().includes(q)) {
        return false;
      }
    }
    if (userLocation) {
      const dist = getDistance(userLocation.lat, userLocation.lng, p.latitude, p.longitude);
      if (dist > radiusKm) return false;
    }
    return true;
  });

  const center = userLocation || (filtered[0]
    ? { lat: filtered[0].latitude, lng: filtered[0].longitude }
    : { lat: 20.5937, lng: 78.9629 }); // India center

  const statusCounts = {};
  filtered.forEach((p) => {
    statusCounts[p.status] = (statusCounts[p.status] || 0) + 1;
  });

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1400px] px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-extrabold text-primary-navy">Public Problem Map</h1>
            <p className="text-ink-soft mt-1">
              {filtered.length} problems with location data
              {filterCategory ? ` in "${filterCategory}"` : ''}
              {filterStatus ? ` (${filterStatus.replace(/_/g, ' ')})` : ''}
            </p>
          </div>
          {!user && (
            <div className="flex gap-3">
              <Link to="/register"><Button size="sm">Get Involved</Button></Link>
              <Link to="/login"><Button size="sm" variant="secondary">Sign In</Button></Link>
            </div>
          )}
        </div>

        {error && <Alert variant="danger" className="mb-4">{error}</Alert>}

        {/* Filters */}
        <Card className="mb-6" padding="md">
          <div className="flex flex-col lg:flex-row lg:items-end gap-4">
            <Input
              label="Search"
              placeholder="Search problems..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="lg:flex-1"
            />
            <Select
              label="Category"
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              options={[
                { value: '', label: 'All Categories' },
                ...CATEGORIES.map((c) => ({ value: c, label: c })),
              ]}
              className="lg:w-48"
            />
            <Select
              label="Status"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              options={[
                { value: '', label: 'All Statuses' },
                { value: 'open', label: 'Open' },
                { value: 'validated', label: 'Validated' },
                { value: 'in_review', label: 'In Review' },
                { value: 'proposal_submitted', label: 'Proposal Submitted' },
                { value: 'in_collaboration', label: 'In Collaboration' },
                { value: 'implemented', label: 'Implemented' },
                { value: 'closed', label: 'Closed' },
              ]}
              className="lg:w-40"
            />
            
            <div className="flex flex-col lg:w-48">
              <label className="block text-sm font-semibold text-ink mb-1.5">Near Me</label>
              <div className="flex items-center">
                <Button 
                  type="button" 
                  variant={userLocation ? 'primary' : 'outline'} 
                  onClick={userLocation ? () => setUserLocation(null) : handleFetchLocation}
                  loading={fetchingLocation}
                  disabled={fetchingLocation}
                  className="w-full whitespace-nowrap"
                >
                  {userLocation ? 'Clear Location' : 'Fetch Location'}
                </Button>
              </div>
            </div>

            {userLocation && (
              <Select
                label="Radius"
                value={radiusKm}
                onChange={(e) => setRadiusKm(Number(e.target.value))}
                options={[
                  { value: 5, label: '5 km' },
                  { value: 10, label: '10 km' },
                  { value: 25, label: '25 km' },
                  { value: 50, label: '50 km' },
                  { value: 100, label: '100 km' },
                ]}
                className="lg:w-32"
              />
            )}
          </div>
        </Card>

        {/* Status legend */}
        <div className="flex flex-wrap gap-2 mb-4">
          {Object.entries(statusCounts).map(([status, count]) => (
            <Badge key={status} variant="outline" className="gap-1">
              <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: STATUS_COLORS[status] || '#ccc' }} />
              {status.replace(/_/g, ' ')} ({count})
            </Badge>
          ))}
        </div>

        {loading ? (
          <PageLoader />
        ) : (
          <Card padding="none" className="overflow-hidden">
            <div className="h-[75vh] w-full">
              <APIProvider apiKey={GOOGLE_MAPS_API_KEY}>
                <Map
                  defaultCenter={center}
                  defaultZoom={5}
                  style={{ width: '100%', height: '100%' }}
                  gestureHandling="greedy"
                >
                  {filtered.map((p) => (
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
                      <div className="space-y-1 min-w-[200px]">
                        <div className="font-bold text-sm">{active.title}</div>
                        <StatusBadge status={active.status} size="sm" />
                        {active.ai_category && (
                          <Badge variant="outline" className="text-xs">{active.ai_category}</Badge>
                        )}
                        {active.ai_priority && (
                          <Badge variant="outline" className="text-xs capitalize">{active.ai_priority} priority</Badge>
                        )}
                        {active.address && (
                          <p className="text-xs text-gray-500">{active.address}</p>
                        )}
                        {user ? (
                          <Link to={`/problems/${active.id}`} className="text-primary text-xs font-semibold block mt-1">
                            View details →
                          </Link>
                        ) : (
                          <Link to={`/login`} className="text-primary text-xs font-semibold block mt-1">
                            Sign in to view details →
                          </Link>
                        )}
                      </div>
                    </InfoWindow>
                  )}
                </Map>
              </APIProvider>
            </div>
          </Card>
        )}

        {/* Stats footer */}
        <div className="mt-6 grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="text-center py-4">
            <div className="text-2xl font-extrabold text-primary-navy">{located.length}</div>
            <div className="text-xs text-ink-muted mt-1">Located Problems</div>
          </Card>
          <Card className="text-center py-4">
            <div className="text-2xl font-extrabold text-primary-navy">
              {filtered.filter((p) => ['open', 'validated', 'in_review'].includes(p.status)).length}
            </div>
            <div className="text-xs text-ink-muted mt-1">Open & Active</div>
          </Card>
          <Card className="text-center py-4">
            <div className="text-2xl font-extrabold text-tag-success">
              {filtered.filter((p) => ['implemented', 'closed'].includes(p.status)).length}
            </div>
            <div className="text-xs text-ink-muted mt-1">Resolved</div>
          </Card>
          <Card className="text-center py-4">
            <div className="text-2xl font-extrabold text-primary">
              {new Set(filtered.map((p) => p.ai_category).filter(Boolean)).size}
            </div>
            <div className="text-xs text-ink-muted mt-1">Categories</div>
          </Card>
        </div>
      </main>
    </div>
  );
}
