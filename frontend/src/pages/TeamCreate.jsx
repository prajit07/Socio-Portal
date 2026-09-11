import { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { problemsApi, teamsApi, universitiesApi } from '../api/client';
import { Button, Card, Input, Select, Alert, PageLoader } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);
const trunc = (s, n = 60) => (s && s.length > n ? `${s.slice(0, n - 1)}…` : s || '');

// Text-based proximity: the institute has district/state (no coordinates),
// problems carry a free-text address — a shared token means "nearby".
const isNearby = (problem, uni) => {
  if (!uni) return false;
  const addr = (problem.address || '').toLowerCase();
  if (!addr) return false;
  return [uni.district, uni.state]
    .map((x) => (x || '').trim().toLowerCase())
    .filter((x) => x.length > 1)
    .some((x) => addr.includes(x) || x.includes(addr.split(',')[0].trim()));
};

export default function TeamCreate() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
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
        // A team belongs to the member's own institute (student/faculty via
        // membership, SPOC via admin link) — never to an arbitrary university.
        const [u, p] = await Promise.all([
          universitiesApi.memberOf(),
          problemsApi.list({ limit: 500 }),
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

  const myUni = unis.find((u) => u.id === universityId) || unis[0] || null;

  const sortedProblems = useMemo(() => {
    const withFlag = problems.map((p) => ({ p, near: isNearby(p, myUni) }));
    withFlag.sort((a, b) => Number(b.near) - Number(a.near));
    return withFlag;
  }, [problems, myUni]);

  const selected = problems.find((p) => p.id === problemId) || null;

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
        {unis.length === 0 && user?.role === 'university_admin' && (
          <Alert variant="warning" className="my-4">
            No institute is registered to your account yet.{' '}
            <Link to="/university/dashboard" className="font-semibold text-primary hover:underline">
              Register your institute first
            </Link>
          </Alert>
        )}
        {unis.length === 0 && user?.role !== 'university_admin' && (
          <Alert variant="warning" className="my-4">
            You aren&apos;t linked to any institute yet. Ask your institute SPOC to add you, or re-register with your institution selected.
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
              options={[
                { value: '', label: 'Select a problem to solve' },
                ...sortedProblems.map(({ p, near }) => ({
                  value: p.id,
                  label: `${p.title || p.id}${p.address ? ` — ${trunc(p.address)}` : ''}${near ? ' · Nearby' : ''}`,
                })),
              ]}
              hint={myUni?.district || myUni?.state ? `Showing problems near ${[myUni.district, myUni.state].filter(Boolean).join(', ')} first.` : undefined}
              required
            />
            {selected && (selected.address || selected.latitude != null) && (
              <div className="rounded-card border border-line bg-bg-soft px-4 py-3 text-sm">
                <div className="font-semibold text-primary-navy">Problem location</div>
                {selected.address && <p className="text-ink-soft mt-1">{selected.address}</p>}
                {selected.latitude != null && selected.longitude != null && (
                  <p className="text-xs text-ink-muted mt-1 font-mono">{selected.latitude.toFixed(4)}, {selected.longitude.toFixed(4)}</p>
                )}
                <Link to="/problems/map" className="text-xs font-semibold text-primary hover:underline">View on public map →</Link>
              </div>
            )}
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
