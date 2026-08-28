import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { proposalsApi } from '../api/client';
import { Button, Card, Input, TextArea, Alert, PageLoader } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);

export default function ProposalEditor() {
  const [params] = useSearchParams();
  const { id: paramId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const id = params.get('id') || paramId || null;
  const teamId = params.get('teamId');
  const problemId = params.get('problemId');
  const isEdit = Boolean(id);

  const [form, setForm] = useState({
    title: '',
    description: '',
    estimated_budget: '',
    estimated_timeline: '',
    document_urls: '',
  });
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isEdit) return;
    (async () => {
      setLoading(true);
      try {
        const p = asData(await proposalsApi.get(id));
        setForm({
          title: p.title || '',
          description: p.description || '',
          estimated_budget: p.estimated_budget ?? '',
          estimated_timeline: p.estimated_timeline ?? '',
          document_urls: Array.isArray(p.document_urls) ? p.document_urls.join(', ') : (p.document_urls || ''),
        });
      } catch (e) {
        setError(e.response?.data?.detail || 'Failed to load proposal.');
      } finally {
        setLoading(false);
      }
    })();
  }, [id, isEdit]);

  const update = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    const payload = {
      title: form.title,
      description: form.description,
      estimated_budget: form.estimated_budget ? Number(form.estimated_budget) : undefined,
      estimated_timeline: form.estimated_timeline || undefined,
      document_urls: form.document_urls
        ? form.document_urls.split(',').map((s) => s.trim()).filter(Boolean)
        : [],
    };
    try {
      if (isEdit) {
        await proposalsApi.update(id, payload);
        navigate(`/university/proposals/${id}`);
      } else {
        const res = await proposalsApi.create({
          team_id: teamId,
          problem_id: problemId,
          ...payload,
        });
        const newId = asData(res).id;
        if (newId) await proposalsApi.submit(newId);
        navigate('/university/dashboard');
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save proposal.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <PageLoader />;

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8 py-8">
        <Link to="/university/dashboard" className="text-sm text-primary hover:underline">← Back to dashboard</Link>
        <h1 className="text-2xl font-extrabold text-primary-navy mt-3">
          {isEdit ? 'Edit Proposal' : 'New Proposal'}
        </h1>
        {!isEdit && (
          <p className="text-sm text-ink-muted mt-1">
            Team: {teamId || '—'} · Problem: {problemId || '—'}
          </p>
        )}

        {error && <Alert variant="danger" className="my-4">{error}</Alert>}

        <Card className="mt-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input label="Title" value={form.title} onChange={update('title')} placeholder="Proposal title" required />
            <TextArea label="Description" rows={6} value={form.description} onChange={update('description')} placeholder="Describe your solution" required />
            <Input label="Estimated Budget" type="number" value={form.estimated_budget} onChange={update('estimated_budget')} placeholder="e.g. 50000" />
            <Input label="Estimated Timeline" value={form.estimated_timeline} onChange={update('estimated_timeline')} placeholder="e.g. 3 months" />
            <Input label="Document URLs (comma separated, optional)" value={form.document_urls} onChange={update('document_urls')} placeholder="https://..." />
            <div className="flex justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => navigate(-1)}>Cancel</Button>
              <Button type="submit" loading={saving}>{isEdit ? 'Save Changes' : 'Create & Submit'}</Button>
            </div>
          </form>
        </Card>
      </main>
    </div>
  );
}
