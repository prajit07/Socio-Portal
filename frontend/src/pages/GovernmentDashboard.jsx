import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { governmentApi } from '../api/client';
import { Card, StatCard, StatusBadge, Alert, PageLoader } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);

export default function GovernmentDashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [boards, setBoards] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [a, b] = await Promise.all([governmentApi.analytics(), governmentApi.leaderboards()]);
        setData(asData(a));
        setBoards(asData(b));
      } catch (e) {
        setError(e.response?.data?.detail || 'Failed to load analytics.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (user?.role !== 'government') return <PageLoader />;
  if (loading) return <PageLoader />;

  const k = data?.kpis || {};
  const maxStatus = Math.max(1, ...(data?.by_status || []).map((x) => x.count));
  const maxCat = Math.max(1, ...(data?.by_category || []).map((x) => x.count));

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-extrabold text-primary-navy">Government Dashboard</h1>
        <p className="text-ink-soft mt-1">Real-time oversight of all societal innovation activity.</p>

        {error && <Alert variant="danger" className="mt-4">{error}</Alert>}

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 my-6">
          <StatCard label="Total Problems" value={k.total_problems || 0} accent="primary" />
          <StatCard label="Open" value={k.open || 0} accent="cyan" />
          <StatCard label="Resolved" value={k.resolved || 0} accent="success" />
          <StatCard label="Active Collaborations" value={k.active_collaborations || 0} accent="primary" />
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard label="Proposals" value={k.proposals || 0} accent="cyan" />
          <StatCard label="Universities" value={k.universities || 0} accent="success" />
          <StatCard label="Industries" value={k.industries || 0} accent="primary" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <h2 className="font-bold text-primary-navy mb-4">Status Breakdown</h2>
            <div className="space-y-3">
              {(data?.by_status || []).map((x) => (
                <div key={x.status} className="flex items-center gap-3">
                  <StatusBadge status={x.status} size="sm" className="w-36" />
                  <div className="flex-1 h-2 rounded-full bg-bg-soft overflow-hidden">
                    <div className="h-full bg-primary" style={{ width: `${(x.count / maxStatus) * 100}%` }} />
                  </div>
                  <span className="text-sm font-semibold text-ink w-8 text-right">{x.count}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <h2 className="font-bold text-primary-navy mb-4">By Category</h2>
            <div className="space-y-3">
              {(data?.by_category || []).map((x) => (
                <div key={x.category} className="flex items-center gap-3">
                  <span className="w-36 text-sm font-semibold text-primary-navy truncate">{x.category}</span>
                  <div className="flex-1 h-2 rounded-full bg-bg-soft overflow-hidden">
                    <div className="h-full bg-tag-blue" style={{ width: `${(x.count / maxCat) * 100}%` }} />
                  </div>
                  <span className="text-sm font-semibold text-ink w-8 text-right">{x.count}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          <Card>
            <h2 className="font-bold text-primary-navy mb-4">Top Universities</h2>
            <div className="space-y-2">
              {(boards?.universities || []).map((u) => (
                <div key={u.id} className="flex items-center justify-between border-b border-line pb-2">
                  <span className="font-semibold text-primary-navy">{u.name}</span>
                  {u.verified && <span className="text-xs text-tag-success font-semibold">verified</span>}
                </div>
              ))}
              {(!boards?.universities || boards.universities.length === 0) && <p className="text-ink-soft">No universities yet.</p>}
            </div>
          </Card>

          <Card>
            <h2 className="font-bold text-primary-navy mb-4">Top Industries</h2>
            <div className="space-y-2">
              {(boards?.industries || []).map((u) => (
                <div key={u.id} className="flex items-center justify-between border-b border-line pb-2">
                  <span className="font-semibold text-primary-navy">{u.name}</span>
                  <span className="text-xs text-ink-muted">{u.type}</span>
                </div>
              ))}
              {(!boards?.industries || boards.industries.length === 0) && <p className="text-ink-soft">No industries yet.</p>}
            </div>
          </Card>
        </div>

        <div className="mt-6">
          <Link to="/problems" className="text-sm font-semibold text-primary hover:underline">View all problems →</Link>
        </div>
      </main>
    </div>
  );
}
