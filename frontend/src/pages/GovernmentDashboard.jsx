import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { problemsApi } from '../api/client';
import { Card, StatCard, StatusBadge, Alert, PageLoader } from '../components/ui';

export default function GovernmentDashboard() {
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => { load(); }, []);

  const load = async () => {
    setLoading(true);
    try {
      const res = await problemsApi.list({ limit: 500 });
      setProblems(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load analytics.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <PageLoader />;

  const byStatus = {};
  problems.forEach((p) => { byStatus[p.status] = (byStatus[p.status] || 0) + 1; });
  const total = problems.length;
  const resolved = (byStatus.implemented || 0) + (byStatus.closed || 0);
  const active = total - resolved - (byStatus.duplicate || 0);

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-extrabold text-primary-navy">Government Dashboard</h1>
        <p className="text-ink-soft mt-1">Real-time oversight of all societal innovation activity.</p>

        {error && <Alert variant="danger" className="mt-4">{error}</Alert>}

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 my-6">
          <StatCard label="Total Problems" value={total} accent="primary" />
          <StatCard label="Active" value={active} accent="cyan" />
          <StatCard label="Resolved" value={resolved} accent="success" />
          <StatCard label="Duplicates" value={byStatus.duplicate || 0} accent="danger" />
        </div>

        <Card>
          <h2 className="font-bold text-primary-navy mb-4">Status Breakdown</h2>
          <div className="space-y-3">
            {Object.entries(byStatus).map(([status, count]) => (
              <div key={status} className="flex items-center gap-3">
                <StatusBadge status={status} size="sm" className="w-40" />
                <div className="flex-1 h-2 rounded-full bg-bg-soft overflow-hidden">
                  <div className="h-full bg-primary" style={{ width: `${total ? (count / total) * 100 : 0}%` }} />
                </div>
                <span className="text-sm font-semibold text-ink w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
          <div className="mt-6">
            <Link to="/problems" className="text-sm font-semibold text-primary hover:underline">View all problems →</Link>
          </div>
        </Card>
      </main>
    </div>
  );
}
