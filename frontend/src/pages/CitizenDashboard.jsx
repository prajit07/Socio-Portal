import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { problemsApi } from '../api/client';
import ProblemDeleteButton from '../components/ProblemDeleteButton';
import { Button, Card, StatCard, StatusBadge, PriorityBadge, Alert, PageLoader, ListSkeleton } from '../components/ui';

const ICONS = {
  total: (
    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-6h13M9 5h13M5 5v.01M5 11v.01M5 17v.01" /></svg>
  ),
  open: (
    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
  ),
  review: (
    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3" /><circle cx="12" cy="12" r="9" /></svg>
  ),
  resolved: (
    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
  ),
};

export default function CitizenDashboard() {
  const { user } = useAuth();
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await problemsApi.list({ limit: 50 });
      setProblems(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load your problems.');
    } finally {
      setLoading(false);
    }
  };

  const stats = {
    total: problems.length,
    open: problems.filter((p) => ['open', 'validated', 'in_review'].includes(p.status)).length,
    review: problems.filter((p) => ['proposal_submitted', 'in_collaboration'].includes(p.status)).length,
    resolved: problems.filter((p) => ['implemented', 'closed'].includes(p.status)).length,
  };

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-extrabold text-primary-navy">
              Welcome, {user?.name?.split(' ')[0] || 'Citizen'}
            </h1>
            <p className="text-ink-soft mt-1">Track the problems you've reported and their progress.</p>
          </div>
          <Link to="/citizen/submit-problem">
            <Button size="lg">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
              Report a Problem
            </Button>
          </Link>
        </div>

        {error && <Alert variant="danger" className="mb-6">{error}</Alert>}

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Reported" value={stats.total} icon={ICONS.total} />
          <StatCard label="Open" value={stats.open} icon={ICONS.open} accent="primary" />
          <StatCard label="In Progress" value={stats.review} icon={ICONS.review} accent="warning" />
          <StatCard label="Resolved" value={stats.resolved} icon={ICONS.resolved} accent="success" />
        </div>

        <h2 className="text-lg font-bold text-primary-navy mb-4">My Problems</h2>
        {loading ? (
          <ListSkeleton count={4} />
        ) : problems.length === 0 ? (
          <Card className="text-center py-12">
            <p className="text-ink-soft">You haven't reported any problems yet.</p>
            <Link to="/citizen/submit-problem" className="mt-4 inline-block">
              <Button>Report your first problem</Button>
            </Link>
          </Card>
        ) : (
           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {problems.map((p) => (
              <Card hover key={p.id}>
                <div className="flex items-start justify-between gap-2">
                  <Link to={`/problems/${p.id}`} className="font-bold text-primary-navy line-clamp-2 hover:underline">
                    {p.title}
                  </Link>
                  <StatusBadge status={p.status} size="sm" />
                </div>
                <p className="text-sm text-ink-soft mt-2 line-clamp-3">{p.description}</p>
                <div className="mt-3 flex items-center justify-between text-xs text-ink-muted">
                  <span>{new Date(p.created_at).toLocaleDateString()}</span>
                  <div className="flex items-center gap-2">
                    {p.ai_priority && <PriorityBadge priority={p.ai_priority} size="sm" />}
                    <ProblemDeleteButton
                      problemId={p.id}
                      canDelete={user?.id === p.submitter_id || user?.role === 'admin'}
                      onDeleted={fetchData}
                    />
                  </div>
                </div>
                {p.ai_category && (
                  <div className="mt-2">
                    <span className="inline-block text-[11px] font-semibold uppercase tracking-wide rounded-full bg-tag-blue/10 text-tag-blue px-2 py-0.5">
                      {p.ai_category}
                    </span>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
