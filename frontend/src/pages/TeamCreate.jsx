import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { problemsApi, teamsApi, universitiesApi } from '../api/client';
import { Button, Card, Input, Select, Alert, PageLoader } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);

export default function TeamCreate() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [problemId, setProblemId] = useState(params.get('problemId') || '');
  const [name, setName] = useState('');
  const [universityId, setUniversityId] = useState('');
  const [unis, setUnis] = useState([]);
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        // SPOC rule: a team always belongs to the SPOC's own institute(s),
        // never to an arbitrary university picked from a global list.
        const [u, p] = await Promise.all([
          universitiesApi.mine(),
          problemsApi.list(),
        ]);
        const mine = asData(u) || [];
        setUnis(mine);
        if (mine.length === 1) setUniversityId(mine[0].id);
        const probs = asData(p) || [];
        setProblems(probs);
        const preset = params.get('problemId');
        if (preset && probs.some((x) => x.id === preset)) setProblemId(preset);
      } catch (e) {
        setError(e.response?.data?.detail || 'Failed to load form data.');
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- one-time form bootstrap
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !problemId || !universityId) return;
    setBusy(true);
    try {
      const res = await teamsApi.create({ problem_id: problemId, name: name.trim(), university_id: universityId });
      navigate(`/university/teams/${asData(res).id}`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create team.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <PageLoader />;

  const canSubmit = name.trim() && problemId && universityId && !busy;

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8 py-8">
        <Link to="/university/dashboard" className="text-sm text-primary hover:underline">← Back to dashboard</Link>
        <h1 className="text-2xl font-extrabold text-primary-navy mt-3">Form a Team</h1>
        <p className="text-ink-soft mt-1 text-sm">Assemble a team from your institute to solve a civic problem. You join as team lead.</p>
        {error && <Alert variant="danger" className="my-4">{error}</Alert>}
        {unis.length === 0 && (
          <Alert variant="warning" className="my-4">
            No institute is registered to your account yet.{' '}
            <Link to="/university/dashboard" className="font-semibold text-primary hover:underline">
              Register your institute first
            </Link>
          </Alert>
        )}
        {problems.length === 0 && (
          <Alert variant="warning" className="my-4">No problems available to form a team for yet.</Alert>
        )}
        <Card className="mt-4">
          <form onSubmit={submit} className="space-y-4">
            <Select
              label="Problem *"
              value={problemId}
              onChange={(e) => setProblemId(e.target.value)}
              options={[{ value: '', label: 'Select a problem to solve' }, ...problems.map((p) => ({ value: p.id, label: `${p.title || p.id} (${p.id})` }))]}
              required
            />
            <Input label="Team Name *" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Innovators Club" required />
            {unis.length === 1 ? (
              <div>
                <label className="block text-sm font-semibold text-ink mb-1.5">Institute</label>
                <p className="rounded-btn border border-line bg-bg-soft px-4 py-2.5 text-sm font-semibold text-primary-navy">{unis[0].name}</p>
              </div>
            ) : (
              <Select
                label="Institute *"
                value={universityId}
                onChange={(e) => setUniversityId(e.target.value)}
                options={[{ value: '', label: 'Select your institute' }, ...unis.map((u) => ({ value: u.id, label: u.name }))]}
                required
              />
            )}
            <div className="flex justify-end">
              <Button type="submit" loading={busy} disabled={!canSubmit}>Create Team</Button>
            </div>
          </form>
        </Card>
      </main>
    </div>
  );
}
