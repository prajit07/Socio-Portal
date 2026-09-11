import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { governmentApi } from '../api/client';
import { Card, StatCard, StatusBadge, Alert, CardSkeleton, ListSkeleton } from '../components/ui';
import { asData } from '../lib/utils';

const STATUS_COLORS = {
  open: '#22C7F2',
  validated: '#1E5EFF',
  in_review: '#8B5CF6',
  proposal_submitted: '#6366F1',
  in_collaboration: '#06B6D4',
  prototype: '#06B6D4',
  pilot: '#1B9C68',
  implementation: '#1B9C68',
  implemented: '#8A94A6',
  closed: '#8A94A6',
  duplicate: '#D64550',
  rejected: '#D64550',
};

const CATEGORY_COLORS = [
  '#1E5EFF', '#22C7F2', '#1B9C68', '#F59E0B', '#D64550',
  '#8B5CF6', '#EC4899', '#06B6D4', '#10B981', '#F97316',
];

const PREVIEW_COUNT = 6;

async function fetchDashboardData() {
  const [a, b] = await Promise.all([governmentApi.analytics(), governmentApi.leaderboards()]);
  return { data: asData(a), boards: asData(b) };
}

export default function GovernmentDashboard() {
  const [data, setData] = useState(null);
  const [boards, setBoards] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [showAllUnis, setShowAllUnis] = useState(false);
  const [showAllInds, setShowAllInds] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data: d, boards: b } = await fetchDashboardData();
        if (!cancelled) {
          setData(d);
          setBoards(b);
          setError('');
        }
      } catch (e) {
        if (!cancelled) setError(e.response?.data?.detail || 'Failed to load analytics.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const { data: d, boards: b } = await fetchDashboardData();
      setData(d);
      setBoards(b);
      setError('');
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load analytics.');
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-soft">
        <Navbar />
        <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
          <div className="h-8 w-64 bg-bg-soft rounded animate-pulse mb-2" />
          <div className="h-4 w-80 bg-bg-soft rounded animate-pulse mb-6" />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <CardSkeleton />
            <CardSkeleton />
          </div>
          <ListSkeleton count={2} />
        </main>
      </div>
    );
  }

  const k = data?.kpis || {};
  const maxStatus = Math.max(1, ...(data?.by_status || []).map((x) => x.count));
  const maxCat = Math.max(1, ...(data?.by_category || []).map((x) => x.count));

  const universities = boards?.universities || [];
  const industries = boards?.industries || [];
  const visibleUnis = showAllUnis ? universities : universities.slice(0, PREVIEW_COUNT);
  const visibleInds = showAllInds ? industries : industries.slice(0, PREVIEW_COUNT);

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-extrabold text-primary-navy">Government Dashboard</h1>
            <p className="text-ink-soft mt-1">Real-time oversight of all societal innovation activity.</p>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/gov/analytics" className="text-sm font-semibold text-primary hover:underline">View Analytics &rarr;</Link>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="rounded-btn border border-line px-4 py-2 text-sm font-semibold text-ink-soft hover:bg-bg-soft transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

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
          <StatCard label="Completion Rate" value={`${k.completion_rate || 0}%`} accent="success" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <h2 className="font-bold text-primary-navy mb-4">Status Breakdown</h2>
            <div className="space-y-3">
              {(data?.by_status || []).map((x) => (
                <div key={x.status} className="flex items-center gap-3">
                  <StatusBadge status={x.status} size="sm" className="w-36 shrink-0" />
                  <div className="flex-1 h-2 rounded-full bg-bg-soft overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${(x.count / maxStatus) * 100}%`,
                        backgroundColor: STATUS_COLORS[x.status] || '#8A94A6',
                      }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-ink w-8 text-right">{x.count}</span>
                </div>
              ))}
              {(!data?.by_status || data.by_status.length === 0) && (
                <p className="text-ink-soft text-sm py-4 text-center">No status data available.</p>
              )}
            </div>
          </Card>

          <Card>
            <h2 className="font-bold text-primary-navy mb-4">By Category</h2>
            <div className="space-y-3">
              {(data?.by_category || []).map((x, i) => (
                <div key={x.category} className="flex items-center gap-3">
                  <span className="w-36 text-sm font-semibold text-primary-navy truncate shrink-0">{x.category}</span>
                  <div className="flex-1 h-2 rounded-full bg-bg-soft overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${(x.count / maxCat) * 100}%`,
                        backgroundColor: CATEGORY_COLORS[i % CATEGORY_COLORS.length],
                      }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-ink w-8 text-right">{x.count}</span>
                </div>
              ))}
              {(!data?.by_category || data.by_category.length === 0) && (
                <p className="text-ink-soft text-sm py-4 text-center">No category data available.</p>
              )}
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          <Card>
            <h2 className="font-bold text-primary-navy mb-4">Top Universities</h2>
            <div className="space-y-2">
              {visibleUnis.map((u, i) => (
                <div key={u.id} className="flex items-center justify-between border-b border-line pb-2 last:border-0">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs font-bold text-ink-muted w-5 shrink-0">{i + 1}.</span>
                    <span className="font-semibold text-primary-navy truncate">{u.name}</span>
                  </div>
                  <span className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-ink-muted">{u.member_count ?? 0} members</span>
                    {u.verified && <span className="text-xs text-tag-success font-semibold">verified</span>}
                  </span>
                </div>
              ))}
              {universities.length === 0 && (
                <p className="text-ink-soft text-sm py-4 text-center">No universities yet.</p>
              )}
            </div>
            {universities.length > PREVIEW_COUNT && (
              <button
                onClick={() => setShowAllUnis((v) => !v)}
                className="mt-3 w-full rounded-btn border border-line-soft px-3 py-2 text-sm font-semibold text-primary hover:bg-bg-soft transition-colors"
              >
                {showAllUnis ? 'View Less' : `View More (${universities.length - PREVIEW_COUNT})`}
              </button>
            )}
          </Card>

          <Card>
            <h2 className="font-bold text-primary-navy mb-4">Top Industries</h2>
            <div className="space-y-2">
              {visibleInds.map((u, i) => (
                <div key={u.id} className="flex items-center justify-between border-b border-line pb-2 last:border-0">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs font-bold text-ink-muted w-5 shrink-0">{i + 1}.</span>
                    <span className="font-semibold text-primary-navy truncate">{u.name}</span>
                  </div>
                  <span className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-ink-muted">{u.collaboration_count ?? 0} collabs</span>
                    {u.type && <span className="text-xs text-ink-muted">{u.type}</span>}
                  </span>
                </div>
              ))}
              {industries.length === 0 && (
                <p className="text-ink-soft text-sm py-4 text-center">No industries yet.</p>
              )}
            </div>
            {industries.length > PREVIEW_COUNT && (
              <button
                onClick={() => setShowAllInds((v) => !v)}
                className="mt-3 w-full rounded-btn border border-line-soft px-3 py-2 text-sm font-semibold text-primary hover:bg-bg-soft transition-colors"
              >
                {showAllInds ? 'View Less' : `View More (${industries.length - PREVIEW_COUNT})`}
              </button>
            )}
          </Card>
        </div>
      </main>
    </div>
  );
}
