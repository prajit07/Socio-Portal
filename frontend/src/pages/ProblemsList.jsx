import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { problemsApi } from '../api/client';
import { Input, Select, Card, Button, StatusBadge, PriorityBadge, Alert, ListSkeleton } from '../components/ui';

export default function ProblemsList() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ status: '', ai_category: '', ai_priority: '' });
  const STATUS_OPTIONS = [
    { value: '', label: t('All Statuses') },
    { value: 'open', label: t('Open') },
    { value: 'validated', label: t('Validated') },
    { value: 'in_review', label: t('In Review') },
    { value: 'proposal_submitted', label: t('Proposal Submitted') },
    { value: 'in_collaboration', label: t('In Collaboration') },
    { value: 'prototype', label: t('Prototype') },
    { value: 'pilot', label: t('Pilot') },
    { value: 'implemented', label: t('Implemented') },
    { value: 'closed', label: t('Closed') },
    { value: 'duplicate', label: t('Duplicate') },
  ];
// Citizens previously saw only their own reports here; the public explorer
  // must show everything, so default to all with an opt-in "Mine only" toggle.
  const [mineOnly, setMineOnly] = useState(false);
  // Debounce text input: without this every keystroke fires GET /problems.
  const [debounced, setDebounced] = useState(filters);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(filters), 400);
    return () => clearTimeout(t);
  }, [filters]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit: 50 };
      if (debounced.status) params.status = debounced.status;
      if (debounced.ai_category.trim()) params.ai_category = debounced.ai_category.trim();
      if (debounced.ai_priority) params.ai_priority = debounced.ai_priority;
      if (user?.role === 'citizen' && mineOnly) params.mine_only = true;
      const res = await problemsApi.list(params);
      setProblems(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || t('Failed to load problems.'));
    } finally {
      setLoading(false);
    }
  }, [debounced, mineOnly, user?.role]);

  // eslint-disable-next-line react/set-state-in-effect -- refetch from server when filters change
  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { document.title = t('Problems — Socio Connect'); }, []);

  // Industry users: API already filters by domain tags; show a hint banner
  const isIndustry = user?.role === 'industry';

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl font-extrabold text-primary-navy">
              {t('Problem Explorer')}
            </h1>
            <p className="text-ink-soft mt-1">
              {isIndustry
                ? t('Problems matched to your domain tags.')
                : t('Browse and discover problems across communities. Public — no login required to view.')}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {user?.role === 'citizen' && (
              <label className="flex items-center gap-2 text-sm font-semibold text-ink-soft cursor-pointer">
                <input
                  type="checkbox"
                  checked={mineOnly}
                  onChange={(e) => setMineOnly(e.target.checked)}
                  className="h-4 w-4 accent-primary"
                />
                {t('Mine only')}
              </label>
            )}
            {!user && (
              <Link to="/problems/map">
                <Button variant="secondary" size="sm">{t('View map')}</Button>
              </Link>
            )}
          </div>
        </div>

        {error && <Alert variant="danger" className="mb-6">{error}</Alert>}

        <Card className="mb-6" padding="md">
          <div className="flex flex-col lg:flex-row lg:items-end gap-4">
            <Select
              label={t('Status')}
              options={STATUS_OPTIONS}
              value={filters.status}
              onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
              className="lg:w-56"
            />
            <Input
              label={t('Category contains')}
              placeholder={t('e.g. Water, Health')}
              value={filters.ai_category}
              onChange={(e) => setFilters((f) => ({ ...f, ai_category: e.target.value }))}
              className="lg:flex-1"
            />
            <Select
              label={t('Priority')}
              options={[
                { value: '', label: t('Any priority') },
                { value: 'low', label: t('Low') },
                { value: 'medium', label: t('Medium') },
                { value: 'high', label: t('High') },
                { value: 'critical', label: t('Critical') },
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
          <Card className="text-center py-12 text-ink-soft">{t('No problems match your filters.')}</Card>
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
                      {t(p.ai_category)}
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
