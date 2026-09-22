import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { collaborationsApi } from '../api/client';
import { Button, Card, Input, TextArea, Select, StatusBadge, Alert, PageLoader } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);
const STAGES = ['interested', 'funding', 'prototype', 'pilot', 'implementation', 'impact_logged'];
export default function CollaborationWorkspace() {
  const { t } = useTranslation();
  const ENGAGEMENT_TYPES = [
    { value: 'express_interest', label: t('Express Interest') },
    { value: 'fund', label: t('Fund') },
    { value: 'co_develop', label: t('Co-Develop') },
  ];
  const FUNDING_STATUS = [
    { value: 'none', label: t('None') },
    { value: 'committed', label: t('Committed') },
    { value: 'disbursed', label: t('Disbursed') },
  ];
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
  const [testingOutcomes, setTestingOutcomes] = useState('');
  const [startupCreated, setStartupCreated] = useState(false);
  const [fundingStatus, setFundingStatus] = useState('none');
  const [ipFile, setIpFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const c = asData(await collaborationsApi.get(id));
      setCollab(c);
      setStage(c.stage || 'interested');
      setFundingStatus(c.funding_status || 'none');
      setTestingOutcomes(c.testing_outcomes || '');
      setStartupCreated(!!c.startup_created);
    } catch (e) {
      setError(e.response?.data?.detail || t('Failed to load collaboration.'));
    } finally {
      setLoading(false);
    }
  }, [id]);

  // eslint-disable-next-line react/set-state-in-effect -- initial server data fetch
  useEffect(() => { load(); }, [load]);

  const guard = () => {
    if (user?.role !== 'industry') { setError(t('Only industry partners can update collaborations.')); return false; }
    return true;
  };

  const updateStage = async () => {
    if (!guard()) return;
    setBusy(true);
    try { await collaborationsApi.update(id, { stage }); setError(''); }
    catch (e) { setError(e.response?.data?.detail || t('Failed to update stage.')); }
    finally { setBusy(false); }
  };

  const setEngagement = async (engagementType) => {
    if (!guard()) return;
    setBusy(true);
    try {
      // A committed (non-express) engagement typically means the collab leaves
      // "interested" — promote the stage to funding for fund/co-develop.
      const patch = { engagement_type: engagementType };
      if (engagementType !== 'express_interest' && collab.stage === 'interested') patch.stage = 'funding';
      await collaborationsApi.update(id, patch);
      setError('');
      await load();
    } catch (e) { setError(e.response?.data?.detail || t('Failed to update engagement.')); }
    finally { setBusy(false); }
  };

  const saveFunding = async () => {
    if (!guard()) return;
    setBusy(true);
    try {
      await collaborationsApi.update(id, { funding_status: fundingStatus, testing_outcomes: testingOutcomes, startup_created: startupCreated });
      setError('');
    } catch (e) { setError(e.response?.data?.detail || t('Failed to save funding/testing info.')); }
    finally { setBusy(false); }
  };

  const uploadIp = async (e) => {
    e.preventDefault();
    if (!ipFile || !ipType.trim() || !guard()) return;
    setBusy(true);
    try {
      await collaborationsApi.uploadIpDocument(id, ipFile, ipType, 'filed', ipRef || null);
      setIpFile(null); setIpType(''); setIpRef('');
      setError('');
      await load();
    } catch (err) { setError(err.response?.data?.detail || t('Failed to upload IP document.')); }
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
    } catch (e) { setError(e.response?.data?.detail || t('Failed to add milestone.')); }
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
    } catch (e) { setError(e.response?.data?.detail || t('Failed to add impact report.')); }
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
    } catch (e) { setError(e.response?.data?.detail || t('Failed to add IP record.')); }
    finally { setBusy(false); }
  };

  if (loading) return <PageLoader />;

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <Link to="/industry/dashboard" className="text-sm text-primary hover:underline">{t('← Back to industry portal')}</Link>

        {error && <Alert variant="danger" className="my-4">{error}</Alert>}

        {collab && (
          <>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mt-4 mb-6">
              <div>
                <h1 className="text-2xl font-extrabold text-primary-navy">{t('Collaboration')}</h1>
                <p className="text-sm text-ink-muted mt-1">
                  {t('Proposal:')} {collab.proposal_id} · {t('Engagement:')} {collab.engagement_type || 'express_interest'}
                  {collab.funding_status ? ` · ${t('Funding:')} ${collab.funding_status}` : ''}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant={collab.engagement_type === 'fund' ? 'primary' : 'ghost'}
                  size="sm"
                  loading={busy}
                  onClick={() => setEngagement('fund')}
                  disabled={user?.role !== 'industry'}
                >{t('Fund')}</Button>
                <Button
                  variant={collab.engagement_type === 'co_develop' ? 'primary' : 'ghost'}
                  size="sm"
                  loading={busy}
                  onClick={() => setEngagement('co_develop')}
                  disabled={user?.role !== 'industry'}
                >{t('Co-Develop')}</Button>
              </div>
            </div>

            <Card className="mb-6">
              <h2 className="font-bold text-primary-navy mb-3">{t('Engagement & Testing')}</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Select
                  label={t('Engagement Type')}
                  value={collab.engagement_type || 'express_interest'}
                  onChange={(e) => setEngagement(e.target.value)}
                  options={ENGAGEMENT_TYPES}
                  disabled={user?.role !== 'industry'}
                />
                <Select
                  label={t('Funding Status')}
                  value={fundingStatus}
                  onChange={(e) => setFundingStatus(e.target.value)}
                  options={FUNDING_STATUS}
                  disabled={user?.role !== 'industry'}
                />
                <label className="flex items-end gap-2 pb-2">
                  <input
                    type="checkbox"
                    checked={startupCreated}
                    onChange={(e) => setStartupCreated(e.target.checked)}
                    className="h-4 w-4 accent-[var(--color-primary)]"
                    disabled={user?.role !== 'industry'}
                  />
                  <span className="text-sm font-medium text-ink">{t('Startup created')}</span>
                </label>
              </div>
              <div className="mt-4">
                <TextArea
                  label={t('Testing Outcomes')}
                  rows={3}
                  value={testingOutcomes}
                  onChange={(e) => setTestingOutcomes(e.target.value)}
                  placeholder={t('Pilot / field-trial results, adoption feedback, co-development milestones...')}
                  disabled={user?.role !== 'industry'}
                />
              </div>
              <div className="mt-4">
                <Button size="sm" loading={busy} onClick={saveFunding} disabled={user?.role !== 'industry'}>{t('Save Fund & Test Info')}</Button>
                <div className="flex items-end gap-3 mt-4">
                  <Select
                    label={t('Stage')}
                    value={stage}
                    onChange={(e) => setStage(e.target.value)}
                    options={STAGES.map((s) => ({ value: s, label: t(s.replace('_', ' ')) }))}
                  />
                  <Button size="sm" loading={busy} onClick={updateStage} disabled={user?.role !== 'industry'}>{t('Update')}</Button>
                </div>
              </div>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <h2 className="font-bold text-primary-navy mb-3">{t('Milestones')}</h2>
                <div className="space-y-2 mb-4">
                  {(collab.milestones || []).map((m) => (
                    <div key={m.id} className="flex items-center justify-between gap-2 border-b border-line pb-2">
                      <div>
                        <p className="font-semibold text-primary-navy">{m.title}</p>
                        <p className="text-xs text-ink-muted">{t('Due:')} {m.due_date || '—'} · {m.status}</p>
                      </div>
                      <StatusBadge status={m.status} size="sm" />
                    </div>
                  ))}
                  {(!collab.milestones || collab.milestones.length === 0) && (
                    <p className="text-sm text-ink-soft">{t('No milestones yet.')}</p>
                  )}
                </div>
                <form onSubmit={addMilestone} className="space-y-3">
                  <Input label={t('Milestone Title')} value={mTitle} onChange={(e) => setMTitle(e.target.value)} placeholder={t('e.g. Prototype build')} />
                  <Input label={t('Due Date')} type="date" value={mDue} onChange={(e) => setMDue(e.target.value)} />
                  <TextArea label={t('Description')} rows={2} value={mDesc} onChange={(e) => setMDesc(e.target.value)} />
                  <Button type="submit" size="sm" loading={busy} disabled={user?.role !== 'industry'}>{t('Add Milestone')}</Button>
                </form>
              </Card>

              <div className="space-y-6">
                <Card>
                  <h2 className="font-bold text-primary-navy mb-3">{t('Impact Report')}</h2>
                  <form onSubmit={addImpact} className="space-y-3">
                    <Input label={t('Beneficiaries Count')} type="number" value={ben} onChange={(e) => setBen(e.target.value)} placeholder={t('e.g. 1200')} />
                    <Input label={t('District')} value={district} onChange={(e) => setDistrict(e.target.value)} placeholder={t('e.g. Delhi')} />
                    <TextArea label={t('Impact Summary')} rows={3} value={impact} onChange={(e) => setImpact(e.target.value)} />
                    <Button type="submit" size="sm" loading={busy} disabled={user?.role !== 'industry'}>{t('Add Impact Report')}</Button>
                  </form>
                  <div className="mt-4 space-y-2">
                    {(collab.impact_reports || []).map((r) => (
                      <div key={r.id} className="text-sm border-b border-line pb-2">
                        <p className="font-semibold text-primary-navy">{r.beneficiaries_count} {t('beneficiaries')} · {r.district || '—'}</p>
                        <p className="text-ink-soft">{r.impact_summary}</p>
                      </div>
                    ))}
                  </div>
                </Card>

                <Card>
                  <h2 className="font-bold text-primary-navy mb-3">{t('IP Records')}</h2>
                  <form onSubmit={addIp} className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <Input label={t('Type')} value={ipType} onChange={(e) => setIpType(e.target.value)} placeholder={t('patent / copyright')} />
                      <Input label={t('Reference No.')} value={ipRef} onChange={(e) => setIpRef(e.target.value)} placeholder={t('optional')} />
                    </div>
                    <Button type="submit" size="sm" variant="ghost" loading={busy} disabled={user?.role !== 'industry'}>{t('Add IP Record (text)')}</Button>
                  </form>
                  <form onSubmit={uploadIp} className="space-y-3 mt-4 border-t border-line pt-4">
                    <p className="text-xs text-ink-muted">{t('Attach an actual IP document (patent/copyright filing).')}</p>
                    <Input
                      label={t('Document')}
                      type="file"
                      accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.txt"
                      onChange={(e) => setIpFile(e.target.files?.[0] || null)}
                    />
                    <div className="grid grid-cols-2 gap-3">
                      <Input label={t('IP Type')} value={ipType} onChange={(e) => setIpType(e.target.value)} placeholder={t('patent / copyright')} />
                      <Input label={t('Reference No.')} value={ipRef} onChange={(e) => setIpRef(e.target.value)} placeholder={t('optional')} />
                    </div>
                    <Button type="submit" size="sm" loading={busy} disabled={user?.role !== 'industry' || !ipFile}>{t('Upload IP Document')}</Button>
                  </form>
                  <div className="mt-4 space-y-2">
                    {(collab.ip_records || []).map((r) => (
                      <div key={r.id} className="text-sm border-b border-line pb-2">
                        <p className="font-semibold text-primary-navy">{r.type} · {r.status}</p>
                        <p className="text-ink-muted">{r.reference_no || '—'}</p>
                        {r.file_url && (
                          <a href={r.file_url} target="_blank" rel="noreferrer" className="text-xs text-primary hover:underline">{t('View document')}</a>
                        )}
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