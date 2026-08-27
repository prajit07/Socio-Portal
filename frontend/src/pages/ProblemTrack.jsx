import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { problemsApi, aiApi } from '../api/client';
import { Button, Card, StatusBadge, PriorityBadge, Badge, Alert, PageLoader } from '../components/ui';

const TIMELINE = [
  { key: 'pending_validation', label: 'Submitted' },
  { key: 'validated', label: 'Validated' },
  { key: 'open', label: 'Open & Routed' },
  { key: 'in_review', label: 'In Review' },
  { key: 'proposal_submitted', label: 'Proposal Submitted' },
  { key: 'in_collaboration', label: 'In Collaboration' },
  { key: 'prototype', label: 'Prototype' },
  { key: 'pilot', label: 'Pilot' },
  { key: 'implemented', label: 'Implemented' },
];

const ORDER = ['pending_validation', 'validated', 'open', 'in_review', 'proposal_submitted', 'in_collaboration', 'prototype', 'pilot', 'implemented', 'closed'];

function Timeline({ status }) {
  const idx = ORDER.indexOf(status);
  return (
    <ol className="relative border-l border-line ml-3 space-y-4">
      {TIMELINE.map((step, i) => {
        const reached = idx >= ORDER.indexOf(step.key);
        return (
          <li key={step.key} className="ml-4">
            <span className={`absolute -left-[9px] flex h-4 w-4 items-center justify-center rounded-full ${reached ? 'bg-primary' : 'bg-line'}`} />
            <p className={`text-sm font-semibold ${reached ? 'text-primary-navy' : 'text-ink-muted'}`}>{step.label}</p>
          </li>
        );
      })}
    </ol>
  );
}

export default function ProblemTrack() {
  const { id } = useParams();
  const { user } = useAuth();
  const [problem, setProblem] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [solutions, setSolutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => { load(); }, [id]);

  const load = async () => {
    setLoading(true);
    try {
      const [p, ev, sol] = await Promise.all([
        problemsApi.get(id),
        problemsApi.listEvidence(id).catch(() => ({ data: [] })),
        problemsApi.solutions.list(id).catch(() => ({ data: [] })),
      ]);
      setProblem(p.data);
      setEvidence(ev.data || []);
      setSolutions(sol.data || []);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load problem.');
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async () => {
    setAnalyzing(true);
    try {
      await aiApi.analyze(id);
      await load();
    } catch (e) {
      setError(e.response?.data?.detail || 'Analysis failed.');
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) return <PageLoader />;
  if (error && !problem) return (
    <div className="min-h-screen bg-bg-soft"><Navbar /><main className="mx-auto max-w-3xl px-4 py-12"><Alert variant="danger">{error}</Alert><Link to="/problems" className="mt-4 inline-block"><Button>Back to Problems</Button></Link></main></div>
  );
  if (!problem) return null;

  const isOwner = problem.submitter_id === user?.id;

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1100px] px-4 sm:px-6 lg:px-8 py-8">
        <Link to="/problems" className="inline-flex items-center gap-1 text-sm text-primary hover:underline mb-6">
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          Back to Problems
        </Link>

        {error && <Alert variant="danger" className="mb-6">{error}</Alert>}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <StatusBadge status={problem.status} />
                {problem.ai_priority && <PriorityBadge priority={problem.ai_priority} />}
                {problem.ai_category && <Badge color="primary">{problem.ai_category}</Badge>}
              </div>
              <h1 className="text-2xl font-extrabold text-primary-navy">{problem.title}</h1>
              <p className="mt-3 text-ink-soft whitespace-pre-wrap">{problem.description}</p>

              {problem.address && (
                <div className="mt-4 flex items-start gap-2 text-sm text-ink-soft bg-bg-soft rounded-card p-3">
                  <svg className="h-5 w-5 text-primary mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a2 2 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                  <div><div className="font-semibold text-primary-navy">Location</div>{problem.address}{problem.latitude && <div className="text-xs text-ink-muted">{problem.latitude}, {problem.longitude}</div>}</div>
                </div>
              )}

              {problem.ai_tags?.length > 0 && (
                <div className="mt-4">
                  <div className="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-2">AI Tags</div>
                  <div className="flex flex-wrap gap-2">
                    {problem.ai_tags.map((t) => <Badge key={t} variant="outline">{t}</Badge>)}
                  </div>
                </div>
              )}

              {problem.ai_duplicate_of && (
                <Alert variant="warning" className="mt-4">
                  This problem was flagged as a possible duplicate of{' '}
                  <Link to={`/problems/${problem.ai_duplicate_of}`} className="font-semibold underline">{problem.ai_duplicate_of}</Link>.
                </Alert>
              )}
            </Card>

            {/* Evidence */}
            <Card>
              <h2 className="font-bold text-primary-navy mb-3">Evidence ({evidence.length})</h2>
              {evidence.length === 0 ? (
                <p className="text-sm text-ink-muted">No evidence uploaded yet.</p>
              ) : (
                <ul className="space-y-2">
                  {evidence.map((e) => (
                    <li key={e.id} className="flex items-center justify-between border border-line rounded-card p-3">
                      <div className="flex items-center gap-3">
                        <Badge color="navy">{e.type}</Badge>
                        <a href={e.file_url} target="_blank" rel="noreferrer" className="text-sm text-primary hover:underline">{e.file_url?.split('/').pop()}</a>
                      </div>
                      {e.type === 'audio' && e.file_url && (
                        <audio controls src={e.file_url} className="h-8" />
                      )}
                    </li>
                  ))}
                </ul>
              )}
              {evidence.find((e) => e.transcript) && (
                <div className="mt-3">
                  <div className="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-1">Transcripts</div>
                  {evidence.filter((e) => e.transcript).map((e) => (
                    <p key={e.id} className="text-sm text-ink-soft bg-bg-soft rounded-card p-3 mb-2">{e.transcript}</p>
                  ))}
                </div>
              )}
            </Card>

            {/* Solutions / Proposals preview */}
            <Card>
              <h2 className="font-bold text-primary-navy mb-3">Proposals ({solutions.length})</h2>
              {solutions.length === 0 ? (
                <p className="text-sm text-ink-muted">No proposals yet. University teams will draft these in the next phase.</p>
              ) : (
                <ul className="space-y-3">
                  {solutions.map((s) => (
                    <li key={s.id} className="border border-line rounded-card p-3">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-primary-navy">{s.title}</span>
                        <StatusBadge status={s.status} size="sm" />
                      </div>
                      <p className="text-sm text-ink-soft mt-1 line-clamp-2">{s.description}</p>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <h3 className="font-bold text-primary-navy mb-3">Progress</h3>
              <Timeline status={problem.status} />
              {isOwner && (
                <Button variant="secondary" size="sm" className="mt-4 w-full" onClick={runAnalysis} loading={analyzing}>
                  Re-run AI Analysis
                </Button>
              )}
            </Card>
            <Card>
              <h3 className="font-bold text-primary-navy mb-2">Submitted</h3>
              <p className="text-sm text-ink-soft">{new Date(problem.created_at).toLocaleString()}</p>
              <p className="text-xs text-ink-muted mt-1 font-mono">{problem.id}</p>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
