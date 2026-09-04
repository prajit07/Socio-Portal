import { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { problemsApi, collaborationsApi, industriesApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Button, Card, Badge, StatusBadge, Select, PageLoader, Alert } from '../components/ui';
import Navbar from '../components/Navbar';

const roleLabels = {
  citizen: 'Citizen', student: 'Student', faculty: 'Faculty',
  university_admin: 'University Admin', industry: 'Industry',
  government: 'Government', admin: 'Admin',
};

const INDUSTRY_ACTIONS = [
  {
    id: 'interested',
    label: 'Express Interest',
    desc: 'Signal interest to start a conversation',
    icon: '🤝',
    color: 'bg-blue-600 hover:bg-blue-700',
  },
  {
    id: 'funding',
    label: 'Fund Proposal',
    desc: 'Commit funding to this solution',
    icon: '💰',
    color: 'bg-emerald-600 hover:bg-emerald-700',
  },
  {
    id: 'prototype',
    label: 'Co-Develop',
    desc: 'Join as a co-development partner',
    icon: '🔬',
    color: 'bg-purple-600 hover:bg-purple-700',
  },
];

export default function SolutionDetail() {
  const { problemId, solutionId } = useParams();
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [solution, setSolution] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({});

  // Industry-specific state
  const [industry, setIndustry] = useState(null);
  const [existingCollab, setExistingCollab] = useState(null);
  const [actionBusy, setActionBusy] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const r = await problemsApi.solutions.get(problemId, solutionId);
      setSolution(r.data);
      setEditData(r.data);

      // If industry user, load their profile and any existing collaboration
      if (user?.role === 'industry') {
        const indsRes = await industriesApi.list().catch(() => ({ data: [] }));
        const myInd = (indsRes.data || [])[0] || null;
        setIndustry(myInd);
        if (myInd) {
          const collabRes = await collaborationsApi.list().catch(() => ({ data: [] }));
          const collabs = collabRes.data || [];
          const existing = collabs.find((c) => c.proposal_id === solutionId && c.industry_id === myInd.id);
          setExistingCollab(existing || null);
        }
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load solution.');
    } finally {
      setLoading(false);
    }
  }, [problemId, solutionId, user]);

  // eslint-disable-next-line react/set-state-in-effect -- initial server data fetch
  useEffect(() => { if (!authLoading) fetchData(); }, [authLoading, fetchData]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      const d = {
        ...editData,
        tech_stack: typeof editData.tech_stack === 'string'
          ? editData.tech_stack.split(',').map((s) => s.trim()).filter(Boolean)
          : editData.tech_stack,
      };
      await problemsApi.solutions.update(problemId, solutionId, d);
      setEditing(false);
      fetchData();
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to update.');
    }
  };

  const handleIndustryAction = async (stage) => {
    if (!industry) {
      setError('Please create your Industry profile first (Industry Dashboard → Profile tab).');
      return;
    }
    setActionBusy(stage);
    setError('');
    try {
      const res = await collaborationsApi.create({
        proposal_id: solutionId,
        industry_id: industry.id,
        stage,
        notes: '',
      });
      const collabId = res.data?.id || res.data;
      navigate(`/industry/collaborations/${collabId}`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to start collaboration.');
    } finally {
      setActionBusy('');
    }
  };

  const canEdit = user && (solution?.author_id === user.id || ['admin', 'government', 'university_admin', 'faculty'].includes(user.role));

  if (authLoading || loading) return <PageLoader />;
  if (error && !solution) return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="max-w-3xl mx-auto px-4 py-12 text-center">
        <Card className="py-12">
          <h2 className="text-xl font-semibold text-primary-navy">Solution Not Found</h2>
          <p className="text-ink-soft mt-2">{error}</p>
          <Link to={`/problems/${problemId}`} className="mt-4 inline-block">
            <Button>Back to Problem</Button>
          </Link>
        </Card>
      </main>
    </div>
  );

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link to={`/problems/${problemId}`} className="inline-flex items-center gap-1 text-sm text-primary hover:underline mb-6">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Problem
        </Link>

        {error && <Alert variant="danger" className="mb-4">{error}</Alert>}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main card */}
          <div className="lg:col-span-2">
            <Card className="overflow-hidden">
              <div className="h-1 bg-gradient-to-r from-emerald-500 to-teal-500" />
              <div className="p-6 border-b border-line flex justify-between items-start">
                <div>
                  <h1 className="text-2xl font-bold text-primary-navy">{solution.title}</h1>
                  <div className="flex gap-2 mt-2 flex-wrap">
                    <StatusBadge status={solution.status} />
                    <Badge variant="outline">{roleLabels[solution.author?.role] || 'Unknown'}</Badge>
                  </div>
                </div>
                {canEdit && !editing && <Button onClick={() => setEditing(true)}>Edit</Button>}
              </div>

              <div className="p-6">
                {editing ? (
                  <form onSubmit={handleUpdate} className="space-y-4">
                    <div>
                      <label className="block text-sm font-semibold text-ink mb-1">Title *</label>
                      <input value={editData.title} onChange={(e) => setEditData({ ...editData, title: e.target.value })} required className="w-full px-4 py-2.5 rounded-lg border border-line focus:border-primary focus:ring-2 focus:ring-primary/20 text-sm" />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-ink mb-1">Description *</label>
                      <textarea value={editData.description} onChange={(e) => setEditData({ ...editData, description: e.target.value })} required rows={4} className="w-full px-4 py-2.5 rounded-lg border border-line focus:border-primary focus:ring-2 focus:ring-primary/20 text-sm" />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-ink mb-1">Approach</label>
                      <textarea value={editData.approach || ''} onChange={(e) => setEditData({ ...editData, approach: e.target.value })} rows={3} className="w-full px-4 py-2.5 rounded-lg border border-line focus:border-primary focus:ring-2 focus:ring-primary/20 text-sm" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-semibold text-ink mb-1">Tech Stack</label>
                        <input value={Array.isArray(editData.tech_stack) ? editData.tech_stack.join(', ') : editData.tech_stack || ''} onChange={(e) => setEditData({ ...editData, tech_stack: e.target.value })} className="w-full px-4 py-2.5 rounded-lg border border-line focus:border-primary focus:ring-2 focus:ring-primary/20 text-sm" placeholder="React, Python, FastAPI" />
                      </div>
                      <Select label="Status" value={editData.status} onChange={(e) => setEditData({ ...editData, status: e.target.value })} options={[
                        { value: 'draft', label: 'Draft' }, { value: 'submitted', label: 'Submitted' },
                        { value: 'under_review', label: 'Under Review' }, { value: 'accepted', label: 'Accepted' },
                        { value: 'rejected', label: 'Rejected' },
                      ]} />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-semibold text-ink mb-1">Timeline</label>
                        <input value={editData.estimated_timeline || ''} onChange={(e) => setEditData({ ...editData, estimated_timeline: e.target.value })} className="w-full px-4 py-2.5 rounded-lg border border-line focus:border-primary focus:ring-2 focus:ring-primary/20 text-sm" placeholder="3 months" />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-ink mb-1">Budget</label>
                        <input value={editData.estimated_budget || ''} onChange={(e) => setEditData({ ...editData, estimated_budget: e.target.value })} className="w-full px-4 py-2.5 rounded-lg border border-line focus:border-primary focus:ring-2 focus:ring-primary/20 text-sm" placeholder="₹5,00,000" />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-ink mb-1">GitHub URL</label>
                      <input value={editData.github_url || ''} onChange={(e) => setEditData({ ...editData, github_url: e.target.value })} className="w-full px-4 py-2.5 rounded-lg border border-line focus:border-primary focus:ring-2 focus:ring-primary/20 text-sm" placeholder="https://github.com/..." />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-ink mb-1">Demo URL</label>
                      <input value={editData.demo_url || ''} onChange={(e) => setEditData({ ...editData, demo_url: e.target.value })} className="w-full px-4 py-2.5 rounded-lg border border-line focus:border-primary focus:ring-2 focus:ring-primary/20 text-sm" placeholder="https://..." />
                    </div>
                    <div className="flex justify-end gap-3">
                      <Button variant="secondary" type="button" onClick={() => setEditing(false)}>Cancel</Button>
                      <Button type="submit">Save Changes</Button>
                    </div>
                  </form>
                ) : (
                  <div className="space-y-6">
                    <div>
                      <h3 className="font-semibold text-primary-navy mb-2">Description</h3>
                      <p className="text-ink-soft whitespace-pre-wrap text-sm leading-relaxed">{solution.description}</p>
                    </div>
                    {solution.approach && (
                      <div>
                        <h3 className="font-semibold text-primary-navy mb-2">Approach</h3>
                        <p className="text-ink-soft whitespace-pre-wrap text-sm leading-relaxed">{solution.approach}</p>
                      </div>
                    )}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm border-t border-line pt-4">
                      {solution.tech_stack?.length > 0 && (
                        <div className="col-span-2">
                          <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-1">Tech Stack</p>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {solution.tech_stack.map((t) => <Badge key={t} variant="outline" size="sm">{t}</Badge>)}
                          </div>
                        </div>
                      )}
                      {solution.estimated_timeline && (
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-1">Timeline</p>
                          <p className="font-medium text-primary-navy">{solution.estimated_timeline}</p>
                        </div>
                      )}
                      {solution.estimated_budget && (
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-1">Budget</p>
                          <p className="font-medium text-primary-navy">{solution.estimated_budget}</p>
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      {solution.github_url && (
                        <a href={solution.github_url} target="_blank" rel="noopener noreferrer">
                          <Button variant="secondary" size="sm">🐙 GitHub</Button>
                        </a>
                      )}
                      {solution.demo_url && (
                        <a href={solution.demo_url} target="_blank" rel="noopener noreferrer">
                          <Button size="sm">🚀 Live Demo</Button>
                        </a>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </div>

          {/* Sidebar — Industry actions */}
          <div className="space-y-4">
            {user?.role === 'industry' && (
              <Card>
                <h3 className="font-bold text-primary-navy mb-1">Industry Actions</h3>
                <p className="text-xs text-ink-soft mb-4">Partner with this university team to bring this solution to life.</p>

                {existingCollab ? (
                  <div className="space-y-3">
                    <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-sm text-emerald-700 font-semibold text-center">
                      ✅ Active Collaboration
                    </div>
                    <p className="text-xs text-ink-muted text-center">Stage: <span className="font-semibold capitalize">{existingCollab.stage.replace('_', ' ')}</span></p>
                    <Link to={`/industry/collaborations/${existingCollab.id}`} className="block">
                      <Button className="w-full">Open Workspace →</Button>
                    </Link>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {INDUSTRY_ACTIONS.map((action) => (
                      <button
                        key={action.id}
                        onClick={() => handleIndustryAction(action.id)}
                        disabled={!!actionBusy}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-white text-sm font-semibold transition ${action.color} disabled:opacity-60`}
                      >
                        <span className="text-xl">{action.icon}</span>
                        <div className="text-left">
                          <div>{actionBusy === action.id ? 'Processing…' : action.label}</div>
                          <div className="text-xs font-normal opacity-80">{action.desc}</div>
                        </div>
                      </button>
                    ))}
                    {!industry && (
                      <p className="text-xs text-ink-muted text-center mt-2">
                        You need an industry profile to collaborate.{' '}
                        <Link to="/industry/dashboard" className="text-primary underline">Create one →</Link>
                      </p>
                    )}
                  </div>
                )}
              </Card>
            )}

            {/* Metadata card */}
            <Card>
              <h3 className="font-bold text-primary-navy mb-3">Details</h3>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-ink-muted">Solution ID</dt>
                  <dd className="font-mono text-xs text-ink-soft">{solution.id}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-muted">Submitted</dt>
                  <dd className="text-ink-soft">{new Date(solution.created_at).toLocaleDateString()}</dd>
                </div>
                <div className="flex justify-between items-center">
                  <dt className="text-ink-muted">Status</dt>
                  <dd><StatusBadge status={solution.status} size="sm" /></dd>
                </div>
              </dl>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}