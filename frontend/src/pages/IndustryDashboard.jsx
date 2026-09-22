import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { problemsApi, industriesApi, collaborationsApi } from '../api/client';
import { Button, Card, Input, Select, StatusBadge, Alert, PageLoader } from '../components/ui';
import DomainMultiSelect from '../components/DomainMultiSelect';
import { useTranslation } from 'react-i18next';

const asData = (r) => (r && r.data !== undefined ? r.data : r);
const INDUSTRY_TYPES = [
  { value: 'startup', label: 'Startup' },
  { value: 'msme', label: 'MSME' },
  { value: 'corporate', label: 'Corporate' },
  { value: 'csr', label: 'CSR Arm' },
  { value: 'research_institution', label: 'Research Institution' },
  { value: 'innovation_hub', label: 'Innovation Hub' },
  { value: 'ngo', label: 'NGO' },
];

export default function IndustryDashboard() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [industry, setIndustry] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [collaborations, setCollaborations] = useState([]);
  const [problems, setProblems] = useState([]);
  const [tags, setTags] = useState([]);
  const [tab, setTab] = useState('proposals');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [createStep, setCreateStep] = useState('details'); // details | domains
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('startup');
  const [newDomains, setNewDomains] = useState([]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const inds = asData(await industriesApi.list()) || [];
      const myInd = inds[0];
      setIndustry(myInd || null);
      const [pr, col, p] = await Promise.all([
        myInd ? industriesApi.proposals(myInd.id) : Promise.resolve([]),
        collaborationsApi.list(),
        problemsApi.list(),
      ]);
      setProposals(asData(pr) || []);
      const allCol = asData(col) || [];
      setCollaborations(myInd ? allCol.filter((c) => c.industry_id === myInd.id) : allCol);
      setProblems(asData(p) || []);
      setTags(myInd?.domain_tags || []);
    } catch (e) {
      setError(e.response?.data?.detail || t('Failed to load dashboard.'));
    } finally {
      setLoading(false);
    }
  }, []);

  // eslint-disable-next-line react/set-state-in-effect -- initial server data fetch on mount
  useEffect(() => { load(); }, [load]);

  const expressInterest = async (proposalId) => {
    if (!industry) { setError(t('Create your industry profile first.')); return; }
    setBusy(true);
    try {
      const res = await collaborationsApi.create({ proposal_id: proposalId, industry_id: industry.id, notes: '' });
      navigate(`/industry/collaborations/${asData(res).id}`);
    } catch (e) {
      setError(e.response?.data?.detail || t('Failed to express interest.'));
    } finally {
      setBusy(false);
    }
  };

  const saveTags = async () => {
    if (!industry) return;
    setBusy(true);
    try {
      await industriesApi.update(industry.id, { domain_tags: tags });
      setError('');
      await load();
    } catch (e) {
      setError(e.response?.data?.detail || t('Failed to save profile.'));
    } finally {
      setBusy(false);
    }
  };

  const createIndustry = async () => {
    if (!newName.trim()) { setError(t('Please enter your organisation name.')); return; }
    if (newDomains.length === 0) { setError(t('Please select at least one domain of interest.')); return; }
    setBusy(true);
    try {
      await industriesApi.create({ name: newName, type: newType, domain_tags: newDomains });
      setError('');
      await load();
      setCreateStep('details');
      setNewName(''); setNewType('startup'); setNewDomains([]);
    } catch (e) {
      setError(e.response?.data?.detail || t('Failed to create industry profile.'));
    } finally {
      setBusy(false);
    }
  };

  if (user?.role !== 'industry') return <PageLoader />;
  if (loading) return <PageLoader />;

  const tabs = [
    { id: 'proposals', label: t('Posted Proposals') },
    { id: 'collab', label: t('My Collaborations') },
    { id: 'feed', label: t('Matched Problems') },
    { id: 'profile', label: t('Profile') },
  ];

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-extrabold text-primary-navy">{t('Industry Portal')}</h1>
          <p className="text-ink-soft mt-1">{t('Discover civic solutions and co-fund impact.')}</p>
        </div>

        {error && <Alert variant="danger" className="mb-6">{error}</Alert>}

        <div className="flex flex-wrap gap-2 mb-6">
          {tabs.map((tb) => (
            <button
              key={tb.id}
              onClick={() => setTab(tb.id)}
              className={`px-4 py-2 rounded-btn text-sm font-semibold transition ${tab === tb.id ? 'bg-primary text-white' : 'bg-white text-ink-soft border border-line'}`}
            >
              {tb.label}
              {tb.id === 'collab' && collaborations.length > 0 && (
                <span className="ml-2 rounded-full bg-tag-blue text-white text-xs px-2 py-0.5">{collaborations.length}</span>
              )}
            </button>
          ))}
        </div>

        {tab === 'proposals' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {proposals.map((pr) => (
              <Card key={pr.id} hover>
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-bold text-primary-navy line-clamp-2">{pr.title}</h3>
                  <StatusBadge status={pr.status} size="sm" />
                </div>
                <p className="text-sm text-ink-soft mt-2 line-clamp-3">{pr.description}</p>
                {pr.estimated_budget != null && (
                  <p className="text-xs text-ink-muted mt-1">{t('Budget: {{budget}}', { budget: pr.estimated_budget })}</p>
                )}
                <Button size="sm" className="mt-3" loading={busy} onClick={() => expressInterest(pr.id)}>
                  {t('Express Interest')}
                </Button>
              </Card>
            ))}
            {proposals.length === 0 && <Card className="text-center py-12 text-ink-soft">{t('No proposals posted yet.')}</Card>}
          </div>
        )}

        {tab === 'collab' && (
          <div className="space-y-4">
            {collaborations.map((c) => (
              <Link key={c.id} to={`/industry/collaborations/${c.id}`}>
                <Card hover className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-bold text-primary-navy">{t('Collaboration')}</p>
                    <p className="text-xs text-ink-muted mt-1">{t('Proposal: {{id}}', { id: c.proposal_id })}</p>
                  </div>
                  <StatusBadge status={c.stage} size="sm" />
                </Card>
              </Link>
            ))}
            {collaborations.length === 0 && <Card className="text-center py-12 text-ink-soft">{t('No collaborations yet.')}</Card>}
          </div>
        )}

        {tab === 'feed' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {problems.map((p) => (
              <Link key={p.id} to={`/problems/${p.id}`}>
                <Card hover>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-bold text-primary-navy line-clamp-2">{p.title}</h3>
                    <StatusBadge status={p.status} size="sm" />
                  </div>
                  <p className="text-sm text-ink-soft mt-2 line-clamp-3">{p.description}</p>
                </Card>
              </Link>
            ))}
            {problems.length === 0 && <Card className="text-center py-12 text-ink-soft">{t('No matched problems.')}</Card>}
          </div>
        )}

        {tab === 'profile' && (
          <div className="max-w-2xl space-y-6">
            {industry ? (
              <Card>
                <h2 className="font-bold text-primary-navy mb-1">{t('Industry Profile')}</h2>
                <p className="text-sm text-ink-soft mb-4">{t('Name:')} <span className="font-semibold text-primary-navy">{industry.name}</span> · {t('Type:')} {industry.type}</p>
                <label className="block text-sm font-semibold text-ink mb-2">{t('Domains of Interest')}</label>
                <DomainMultiSelect selected={tags} onChange={setTags} />
                <div className="mt-4">
                  <Button size="sm" loading={busy} onClick={saveTags}>{t('Save Domains')}</Button>
                </div>
              </Card>
            ) : (
              <Card>
                <h2 className="font-bold text-primary-navy mb-1">{t('Create your industry profile')}</h2>
                <p className="text-sm text-ink-soft mb-4">
                  {t('Step')} {createStep === 'details' ? t('1 of 2') : t('2 of 2')}:{' '}
                  {createStep === 'details' ? t('Organisation details') : t('Select domains of interest')}
                </p>

                {createStep === 'details' ? (
                  <div className="space-y-4">
                    <Input label={t('Organisation Name')} value={newName} onChange={(e) => setNewName(e.target.value)} placeholder={t('e.g. Acme CleanTech')} />
                    <Select
                      label={t('Organisation Type')}
                      value={newType}
                      onChange={(e) => setNewType(e.target.value)}
                      options={INDUSTRY_TYPES.map((o) => ({ value: o.value, label: t(o.label) }))}
                    />
                    <div className="flex justify-end">
                      <Button size="sm" onClick={() => setCreateStep('domains')} disabled={!newName.trim()}>{t('Next')}</Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <label className="block text-sm font-semibold text-ink mb-2">{t('Select all domains you are interested in')}</label>
                    <DomainMultiSelect selected={newDomains} onChange={setNewDomains} />
                    <div className="flex justify-between">
                      <Button size="sm" variant="secondary" onClick={() => setCreateStep('details')}>{t('Back')}</Button>
                      <Button size="sm" loading={busy} onClick={createIndustry}>{t('Create Profile')}</Button>
                    </div>
                  </div>
                )}
              </Card>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
