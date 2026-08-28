import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { problemsApi, industriesApi, collaborationsApi } from '../api/client';
import { Button, Card, Input, StatusBadge, Alert, PageLoader } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);

export default function IndustryDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [industry, setIndustry] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [collaborations, setCollaborations] = useState([]);
  const [problems, setProblems] = useState([]);
  const [tags, setTags] = useState('');
  const [tab, setTab] = useState('proposals');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => { load(); }, []);

  const load = async () => {
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
      setTags((myInd?.domain_tags || []).join(', '));
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load dashboard.');
    } finally {
      setLoading(false);
    }
  };

  const expressInterest = async (proposalId) => {
    if (!industry) { setError('Create your industry profile first.'); return; }
    setBusy(true);
    try {
      const res = await collaborationsApi.create({ proposal_id: proposalId, industry_id: industry.id, notes: '' });
      navigate(`/industry/collaborations/${asData(res).id}`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to express interest.');
    } finally {
      setBusy(false);
    }
  };

  const saveTags = async () => {
    if (!industry) return;
    setBusy(true);
    try {
      await industriesApi.update(industry.id, { domain_tags: tags.split(',').map((s) => s.trim()).filter(Boolean) });
      setError('');
      await load();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save profile.');
    } finally {
      setBusy(false);
    }
  };

  if (user?.role !== 'industry') return <PageLoader />;
  if (loading) return <PageLoader />;

  const tabs = [
    { id: 'proposals', label: 'Posted Proposals' },
    { id: 'collab', label: 'My Collaborations' },
    { id: 'feed', label: 'Matched Problems' },
    { id: 'profile', label: 'Profile' },
  ];

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-extrabold text-primary-navy">Industry Portal</h1>
          <p className="text-ink-soft mt-1">Discover civic solutions and co-fund impact.</p>
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
              {t.id === 'collab' && collaborations.length > 0 && (
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
                  <p className="text-xs text-ink-muted mt-1">Budget: {pr.estimated_budget}</p>
                )}
                <Button size="sm" className="mt-3" loading={busy} onClick={() => expressInterest(pr.id)}>
                  Express Interest
                </Button>
              </Card>
            ))}
            {proposals.length === 0 && <Card className="text-center py-12 text-ink-soft">No proposals posted yet.</Card>}
          </div>
        )}

        {tab === 'collab' && (
          <div className="space-y-4">
            {collaborations.map((c) => (
              <Link key={c.id} to={`/industry/collaborations/${c.id}`}>
                <Card hover className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-bold text-primary-navy">Collaboration</p>
                    <p className="text-xs text-ink-muted mt-1">Proposal: {c.proposal_id}</p>
                  </div>
                  <StatusBadge status={c.stage} size="sm" />
                </Card>
              </Link>
            ))}
            {collaborations.length === 0 && <Card className="text-center py-12 text-ink-soft">No collaborations yet.</Card>}
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
            {problems.length === 0 && <Card className="text-center py-12 text-ink-soft">No matched problems.</Card>}
          </div>
        )}

        {tab === 'profile' && (
          <Card className="max-w-2xl">
            <h2 className="font-bold text-primary-navy mb-3">Industry Profile</h2>
            {industry ? (
              <>
                <p className="text-sm text-ink-soft mb-4">Name: <span className="font-semibold text-primary-navy">{industry.name}</span> · Type: {industry.type}</p>
                <Input label="Domain Tags (comma separated)" value={tags} onChange={(e) => setTags(e.target.value)} placeholder="water, energy, health" />
                <div className="mt-4">
                  <Button size="sm" loading={busy} onClick={saveTags}>Save Profile</Button>
                </div>
              </>
            ) : (
              <p className="text-sm text-ink-soft">No industry profile found. Contact an admin to create one.</p>
            )}
          </Card>
        )}
      </main>
    </div>
  );
}
