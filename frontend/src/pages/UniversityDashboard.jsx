import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { problemsApi, teamsApi, proposalsApi } from '../api/client';
import { Button, Card, StatusBadge, Alert, PageLoader } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);

export default function UniversityDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('problems');
  const [problems, setProblems] = useState([]);
  const [teams, setTeams] = useState([]);
  const [proposals, setProposals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState(null);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [p, t, pr] = await Promise.all([
        problemsApi.list(),
        teamsApi.list(),
        proposalsApi.list(),
      ]);
      setProblems(asData(p) || []);
      setTeams(asData(t) || []);
      setProposals(asData(pr) || []);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load dashboard.');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id) => {
    setBusyId(id);
    try {
      await proposalsApi.approve(id);
      setProposals((prev) => prev.map((x) => (x.id === id ? { ...x, status: 'approved' } : x)));
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to approve proposal.');
    } finally {
      setBusyId(null);
    }
  };

  const handleFormTeam = () => {
    const firstId = problems[0]?.id;
    const pid = firstId || window.prompt('Enter a problem ID to form a team for:');
    navigate(pid ? `/university/teams/new?problemId=${pid}` : '/university/teams/new');
  };

  if (!['university_admin', 'student', 'faculty'].includes(user?.role)) return <PageLoader />;

  const tabs = [
    { id: 'problems', label: 'Problem Feed' },
    { id: 'teams', label: 'My Teams' },
    { id: 'proposals', label: 'My Proposals' },
    { id: 'approvals', label: 'Mentor Approvals' },
  ];

  const submitted = proposals.filter((p) => p.status === 'submitted');

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-extrabold text-primary-navy">
              University Workspace
            </h1>
            <p className="text-ink-soft mt-1">Collaborate on civic problems as {user?.role?.replace('_', ' ')}.</p>
          </div>
          <Button onClick={handleFormTeam}>Form Team</Button>
        </div>

        {error && <Alert variant="danger" className="mb-6">{error}</Alert>}

        <div className="flex flex-wrap gap-2 mb-6">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-btn text-sm font-semibold transition ${tab === t.id ? 'bg-primary text-white' : 'bg-white text-ink-soft border border-line'}`}
            >
              {t.label}
              {t.id === 'approvals' && submitted.length > 0 && (
                <span className="ml-2 rounded-full bg-tag-danger text-white text-xs px-2 py-0.5">{submitted.length}</span>
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <PageLoader />
        ) : tab === 'problems' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {problems.map((p) => (
              <Link key={p.id} to={`/problems/${p.id}`}>
                <Card hover>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-bold text-primary-navy line-clamp-2">{p.title}</h3>
                    <StatusBadge status={p.status} size="sm" />
                  </div>
                  <p className="text-sm text-ink-soft mt-2 line-clamp-3">{p.description}</p>
                  {p.ai_category && (
                    <span className="inline-block mt-2 text-[11px] font-semibold uppercase tracking-wide rounded-full bg-tag-blue/10 text-tag-blue px-2 py-0.5">
                      {p.ai_category}
                    </span>
                  )}
                </Card>
              </Link>
            ))}
          </div>
        ) : tab === 'teams' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {teams.map((t) => (
              <Link key={t.id} to={`/university/teams/${t.id}`}>
                <Card hover>
                  <h3 className="font-bold text-primary-navy">{t.name}</h3>
                  <p className="text-xs text-ink-muted mt-1">Problem: {t.problem_id}</p>
                </Card>
              </Link>
            ))}
            {teams.length === 0 && <Card className="text-center py-12 text-ink-soft">No teams yet.</Card>}
          </div>
        ) : tab === 'proposals' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {proposals.map((pr) => (
              <Link key={pr.id} to={`/university/proposals/${pr.id}`}>
                <Card hover>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-bold text-primary-navy line-clamp-2">{pr.title}</h3>
                    <StatusBadge status={pr.status} size="sm" />
                  </div>
                  <p className="text-xs text-ink-muted mt-1">Problem: {pr.problem_id}</p>
                </Card>
              </Link>
            ))}
            {proposals.length === 0 && <Card className="text-center py-12 text-ink-soft">No proposals yet.</Card>}
          </div>
        ) : (
          <div className="space-y-4">
            {submitted.map((pr) => (
              <Card key={pr.id} className="flex items-center justify-between gap-4">
                <div>
                  <Link to={`/university/proposals/${pr.id}`} className="font-bold text-primary-navy hover:underline">{pr.title}</Link>
                  <p className="text-xs text-ink-muted mt-1">Problem: {pr.problem_id}</p>
                </div>
                <Button size="sm" onClick={() => handleApprove(pr.id)} loading={busyId === pr.id}>Approve</Button>
              </Card>
            ))}
            {submitted.length === 0 && <Card className="text-center py-12 text-ink-soft">No proposals awaiting approval.</Card>}
          </div>
        )}
      </main>
    </div>
  );
}
