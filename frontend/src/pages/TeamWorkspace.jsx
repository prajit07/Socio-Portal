import { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { teamsApi, problemsApi } from '../api/client';
import { Button, Card, Input, Alert, PageLoader, StatusBadge } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);

export default function TeamWorkspace() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [team, setTeam] = useState(null);
  const [problem, setProblem] = useState(null);
  const [userId, setUserId] = useState('');
  const [role, setRole] = useState('member');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [adding, setAdding] = useState(false);

  useEffect(() => { fetchData(); }, [id]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const t = asData(await teamsApi.get(id));
      setTeam(t);
      if (t?.problem_id) {
        try { setProblem(asData(await problemsApi.get(t.problem_id))); } catch { /* ignore */ }
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load team.');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!userId.trim()) return;
    setAdding(true);
    setError('');
    try {
      await teamsApi.addMember(id, { user_id: userId.trim(), role });
      setUserId('');
      setRole('member');
      await fetchData();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to add member.');
    } finally {
      setAdding(false);
    }
  };

  if (loading) return <PageLoader />;

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <Link to="/university/dashboard" className="text-sm text-primary hover:underline">← Back to dashboard</Link>

        {error && <Alert variant="danger" className="my-4">{error}</Alert>}

        {team && (
          <>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mt-4 mb-6">
              <div>
                <h1 className="text-2xl font-extrabold text-primary-navy">{team.name}</h1>
                {problem ? (
                  <Link to={`/problems/${team.problem_id}`} className="text-sm text-primary hover:underline">
                    {problem.title}
                  </Link>
                ) : (
                  <p className="text-sm text-ink-muted">Problem: {team.problem_id}</p>
                )}
              </div>
              <Link to={`/university/proposals/new?teamId=${team.id}&problemId=${team.problem_id}`}>
                <Button>New Proposal</Button>
              </Link>
            </div>

            <h2 className="text-lg font-bold text-primary-navy mb-3">Members</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {(team.members || []).map((m) => (
                <Card key={m.id}>
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <p className="font-semibold text-primary-navy">{m.name || m.email}</p>
                      <p className="text-xs text-ink-muted">{m.email}</p>
                    </div>
                    <Badge role={m.role} />
                  </div>
                </Card>
              ))}
              {(!team.members || team.members.length === 0) && (
                <Card className="text-center py-8 text-ink-soft">No members yet.</Card>
              )}
            </div>

            <Card>
              <h3 className="font-bold text-primary-navy mb-3">Add Member</h3>
              <form onSubmit={handleAdd} className="flex flex-col sm:flex-row gap-3">
                <Input
                  label="User ID"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="User ID"
                  required
                />
                <Input
                  label="Role"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  placeholder="member / lead"
                />
                <div className="flex items-end">
                  <Button type="submit" loading={adding}>Add Member</Button>
                </div>
              </form>
            </Card>
          </>
        )}
      </main>
    </div>
  );
}

function Badge({ role }) {
  return <StatusBadge status={role || 'member'} size="sm" />;
}
