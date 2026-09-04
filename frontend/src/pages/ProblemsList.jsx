import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { problemsApi } from '../api/client';
import { Input, Select, Card, StatusBadge, PriorityBadge, Alert, ListSkeleton } from '../components/ui';

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'open', label: 'Open' },
  { value: 'validated', label: 'Validated' },
  { value: 'in_review', label: 'In Review' },
  { value: 'proposal_submitted', label: 'Proposal Submitted' },
  { value: 'in_collaboration', label: 'In Collaboration' },
  { value: 'prototype', label: 'Prototype' },
  { value: 'pilot', label: 'Pilot' },
  { value: 'implemented', label: 'Implemented' },
  { value: 'closed', label: 'Closed' },
  { value: 'duplicate', label: 'Duplicate' },
];

export default function ProblemsList() {
  const { user } = useAuth();
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ status: '', ai_category: '', ai_priority: '' });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit: 50 };
      if (filters.status) params.status = filters.status;
      if (filters.ai_category) params.ai_category = filters.ai_category;
      if (filters.ai_priority) params.ai_priority = filters.ai_priority;
      const res = await problemsApi.list(params);
      setProblems(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load problems.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // eslint-disable-next-line react/set-state-in-effect -- refetch from server when filters change
  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { document.title = 'Problems — Socio Connect'; }, []);

  // Industry users: API already filters by domain tags; show a hint banner
  const isIndustry = user?.role === 'industry';

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-extrabold text-primary-navy">
            {user?.role === 'citizen' ? 'My Problems' : 'Problem Explorer'}
          </h1>
          <p className="text-ink-soft mt-1">
            {isIndustry
              ? 'Problems matched to your domain tags.'
              : 'Browse and discover problems across communities.'}
          </p>
        </div>

        {error && <Alert variant="danger" className="mb-6">{error}</Alert>}

        <Card className="mb-6" padding="md">
          <div className="flex flex-col lg:flex-row lg:items-end gap-4">
            <Select
              label="Status"
              options={STATUS_OPTIONS}
              value={filters.status}
              onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
              className="lg:w-56"
            />
            <Input
              label="Category contains"
              placeholder="e.g. Water, Health"
              value={filters.ai_category}
              onChange={(e) => setFilters((f) => ({ ...f, ai_category: e.target.value }))}
              className="lg:flex-1"
            />
            <Select
              label="Priority"
              options={[
                { value: '', label: 'Any priority' },
                { value: 'low', label: 'Low' },
                { value: 'medium', label: 'Medium' },
                { value: 'high', label: 'High' },
                { value: 'critical', label: 'Critical' },
              ]}
              value={filters.ai_priority}
              onChange={(e) => setFilters((f) => ({ ...f, ai_priority: e.target.value }))}
              className="lg:w-48"
            />
          </div>
        </Card>

        {loading ? (
          <ListSkeleton count={6} />
        ) : problems.length === 0 ? (
          <Card className="text-center py-12 text-ink-soft">No problems match your filters.</Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {problems.map((p) => (
              <Link key={p.id} to={`/problems/${p.id}`}>
                <Card hover>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-bold text-primary-navy line-clamp-2">{p.title}</h3>
                    <StatusBadge status={p.status} size="sm" />
                  </div>
                  <p className="text-sm text-ink-soft mt-2 line-clamp-3">{p.description}</p>
                  <div className="mt-3 flex items-center justify-between text-xs text-ink-muted">
                    <span>{new Date(p.created_at).toLocaleDateString()}</span>
                    {p.ai_priority && <PriorityBadge priority={p.ai_priority} size="sm" />}
                  </div>
                  {p.ai_category && (
                    <span className="mt-2 inline-block text-[11px] font-semibold uppercase tracking-wide rounded-full bg-tag-blue/10 text-tag-blue px-2 py-0.5">
                      {p.ai_category}
                    </span>
                  )}
                </Card>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
