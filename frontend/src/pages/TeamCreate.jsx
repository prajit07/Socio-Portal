import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { teamsApi, universitiesApi } from '../api/client';
import { Button, Card, Input, Select, Alert, PageLoader } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);

export default function TeamCreate() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [problemId, setProblemId] = useState(params.get('problemId') || '');
  const [name, setName] = useState('');
  const [universityId, setUniversityId] = useState('');
  const [unis, setUnis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const u = asData(await universitiesApi.list()) || [];
        setUnis(u);
        if (u[0]) setUniversityId(u[0].id);
      } catch (e) {
        setError(e.response?.data?.detail || 'Failed to load universities.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !problemId.trim() || !universityId) return;
    setBusy(true);
    try {
      const res = await teamsApi.create({ problem_id: problemId, name, university_id: universityId });
      navigate(`/university/teams/${asData(res).id}`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create team.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <PageLoader />;

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8 py-8">
        <Link to="/university/dashboard" className="text-sm text-primary hover:underline">← Back to dashboard</Link>
        <h1 className="text-2xl font-extrabold text-primary-navy mt-3">Form a Team</h1>
        {error && <Alert variant="danger" className="my-4">{error}</Alert>}
        <Card className="mt-4">
          <form onSubmit={submit} className="space-y-4">
            <Input label="Problem ID" value={problemId} onChange={(e) => setProblemId(e.target.value)} placeholder="problem id" required />
            <Input label="Team Name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Innovators Club" required />
            <Select
              label="University"
              value={universityId}
              onChange={(e) => setUniversityId(e.target.value)}
              options={unis.map((u) => ({ value: u.id, label: u.name }))}
            />
            <div className="flex justify-end">
              <Button type="submit" loading={busy}>Create Team</Button>
            </div>
          </form>
        </Card>
      </main>
    </div>
  );
}
