import { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { collaborationsApi } from '../api/client';
import { Button, Card, Input, TextArea, Select, StatusBadge, Alert, PageLoader } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);
const STAGES = ['interested', 'funding', 'prototype', 'pilot', 'implementation', 'impact_logged'];

export default function CollaborationWorkspace() {
  const { id } = useParams();
  const { user } = useAuth();
  const [collab, setCollab] = useState(null);
  const [stage, setStage] = useState('');
  const [mTitle, setMTitle] = useState('');
  const [mDue, setMDue] = useState('');
  const [mDesc, setMDesc] = useState('');
  const [ben, setBen] = useState('');
  const [impact, setImpact] = useState('');
  const [district, setDistrict] = useState('');
  const [ipType, setIpType] = useState('');
  const [ipRef, setIpRef] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const c = asData(await collaborationsApi.get(id));
      setCollab(c);
      setStage(c.stage || 'interested');
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load collaboration.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [id]);

  const guard = () => {
    if (user?.role !== 'industry') { setError('Only industry partners can update collaborations.'); return false; }
    return true;
  };

  const updateStage = async () => {
    if (!guard()) return;
    setBusy(true);
    try { await collaborationsApi.update(id, { stage }); setError(''); }
    catch (e) { setError(e.response?.data?.detail || 'Failed to update stage.'); }
    finally { setBusy(false); }
  };

  const addMilestone = async (e) => {
    e.preventDefault();
    if (!mTitle.trim() || !guard()) return;
    setBusy(true);
    try {
      await collaborationsApi.addMilestone(id, { title: mTitle, due_date: mDue || null, description: mDesc });
      setMTitle(''); setMDue(''); setMDesc('');
      await load();
    } catch (e) { setError(e.response?.data?.detail || 'Failed to add milestone.'); }
    finally { setBusy(false); }
  };

  const addImpact = async (e) => {
    e.preventDefault();
    if (!impact.trim() || !guard()) return;
    setBusy(true);
    try {
      await collaborationsApi.addImpact(id, {
        beneficiaries_count: Number(ben) || 0,
        impact_summary: impact,
        district: district || null,
        state: null,
      });
      setBen(''); setImpact(''); setDistrict('');
      await load();
    } catch (e) { setError(e.response?.data?.detail || 'Failed to add impact report.'); }
    finally { setBusy(false); }
  };

  const addIp = async (e) => {
    e.preventDefault();
    if (!ipType.trim() || !guard()) return;
    setBusy(true);
    try {
      await collaborationsApi.addIp(id, { type: ipType, status: 'filed', reference_no: ipRef || null });
      setIpType(''); setIpRef('');
      await load();
    } catch (e) { setError(e.response?.data?.detail || 'Failed to add IP record.'); }
    finally { setBusy(false); }
  };

  if (loading) return <PageLoader />;

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <Link to="/industry/dashboard" className="text-sm text-primary hover:underline">← Back to industry portal</Link>

        {error && <Alert variant="danger" className="my-4">{error}</Alert>}

        {collab && (
          <>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mt-4 mb-6">
              <div>
                <h1 className="text-2xl font-extrabold text-primary-navy">Collaboration</h1>
                <p className="text-sm text-ink-muted mt-1">Proposal: {collab.proposal_id}</p>
              </div>
              <div className="flex items-end gap-3">
                <Select
                  label="Stage"
                  value={stage}
                  onChange={(e) => setStage(e.target.value)}
                  options={STAGES.map((s) => ({ value: s, label: s.replace('_', ' ') }))}
                />
                <Button size="sm" loading={busy} onClick={updateStage} disabled={user?.role !== 'industry'}>Update</Button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <h2 className="font-bold text-primary-navy mb-3">Milestones</h2>
                <div className="space-y-2 mb-4">
                  {(collab.milestones || []).map((m) => (
                    <div key={m.id} className="flex items-center justify-between gap-2 border-b border-line pb-2">
                      <div>
                        <p className="font-semibold text-primary-navy">{m.title}</p>
                        <p className="text-xs text-ink-muted">Due: {m.due_date || '—'} · {m.status}</p>
                      </div>
                      <StatusBadge status={m.status} size="sm" />
                    </div>
                  ))}
                  {(!collab.milestones || collab.milestones.length === 0) && (
                    <p className="text-sm text-ink-soft">No milestones yet.</p>
                  )}
                </div>
                <form onSubmit={addMilestone} className="space-y-3">
                  <Input label="Milestone Title" value={mTitle} onChange={(e) => setMTitle(e.target.value)} placeholder="e.g. Prototype build" />
                  <Input label="Due Date" type="date" value={mDue} onChange={(e) => setMDue(e.target.value)} />
                  <TextArea label="Description" rows={2} value={mDesc} onChange={(e) => setMDesc(e.target.value)} />
                  <Button type="submit" size="sm" loading={busy} disabled={user?.role !== 'industry'}>Add Milestone</Button>
                </form>
              </Card>

              <div className="space-y-6">
                <Card>
                  <h2 className="font-bold text-primary-navy mb-3">Impact Report</h2>
                  <form onSubmit={addImpact} className="space-y-3">
                    <Input label="Beneficiaries Count" type="number" value={ben} onChange={(e) => setBen(e.target.value)} placeholder="e.g. 1200" />
                    <Input label="District" value={district} onChange={(e) => setDistrict(e.target.value)} placeholder="e.g. Delhi" />
                    <TextArea label="Impact Summary" rows={3} value={impact} onChange={(e) => setImpact(e.target.value)} />
                    <Button type="submit" size="sm" loading={busy} disabled={user?.role !== 'industry'}>Add Impact Report</Button>
                  </form>
                  <div className="mt-4 space-y-2">
                    {(collab.impact_reports || []).map((r) => (
                      <div key={r.id} className="text-sm border-b border-line pb-2">
                        <p className="font-semibold text-primary-navy">{r.beneficiaries_count} beneficiaries · {r.district || '—'}</p>
                        <p className="text-ink-soft">{r.impact_summary}</p>
                      </div>
                    ))}
                  </div>
                </Card>

                <Card>
                  <h2 className="font-bold text-primary-navy mb-3">IP Records</h2>
                  <form onSubmit={addIp} className="space-y-3">
                    <Input label="Type" value={ipType} onChange={(e) => setIpType(e.target.value)} placeholder="patent / copyright" />
                    <Input label="Reference No." value={ipRef} onChange={(e) => setIpRef(e.target.value)} placeholder="optional" />
                    <Button type="submit" size="sm" loading={busy} disabled={user?.role !== 'industry'}>Add IP Record</Button>
                  </form>
                  <div className="mt-4 space-y-2">
                    {(collab.ip_records || []).map((r) => (
                      <div key={r.id} className="text-sm border-b border-line pb-2">
                        <p className="font-semibold text-primary-navy">{r.type} · {r.status}</p>
                        <p className="text-ink-muted">{r.reference_no || '—'}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
