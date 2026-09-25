import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { teamsApi, problemsApi, usersApi } from '../api/client';
import { Button, Card, Input, Alert, PageLoader, StatusBadge } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);

export default function TeamWorkspace() {
  const { t } = useTranslation();
  const { id } = useParams();
  const [team, setTeam] = useState(null);
  const [problem, setProblem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [adding, setAdding] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [email, setEmail] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const t = asData(await teamsApi.get(id));
      setTeam(t);
      if (t?.problem_id) {
        try { setProblem(asData(await problemsApi.get(t.problem_id))); } catch { /* ignore */ }
      }
    } catch (e) {
      setError(e.response?.data?.detail || t('Failed to load team.'));
    } finally {
      setLoading(false);
    }
  }, [id]);

  // eslint-disable-next-line react/set-state-in-effect -- initial server data fetch
  useEffect(() => { fetchData(); }, [fetchData]);

  const onSearch = async (v) => {
    setQuery(v);
    setError('');
    if (!v.trim() || v.trim().length < 2) { setResults([]); return; }
    setSearching(true);
    try {
      const r = asData(await usersApi.search(v.trim())) || [];
      const memberIds = new Set((team?.members || []).map((m) => m.user_id));
      setResults(r.filter((u) => !memberIds.has(u.id)));
    } catch (e) {
      setError(e.response?.data?.detail || t('Search failed.'));
    } finally {
      setSearching(false);
    }
  };

  const handleAddUser = async (userId, role = 'member') => {
    setAdding(true);
    setError('');
    try {
      await teamsApi.addMember(id, { user_id: userId, role });
      setQuery(''); setResults([]);
      await fetchData();
    } catch (e) {
      setError(e.response?.data?.detail || t('Failed to add member.'));
    } finally {
      setAdding(false);
    }
  };

  const handleAddByEmail = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    setAdding(true);
    setError('');
    try {
      await teamsApi.addMember(id, { email: email.trim(), role: 'member' });
      setEmail('');
      await fetchData();
    } catch (e) {
      setError(e.response?.data?.detail || t('Failed to add member.'));
    } finally {
      setAdding(false);
    }
  };

  if (loading) return <PageLoader />;

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <Link to="/university/dashboard" className="text-sm text-primary hover:underline">{t('← Back to dashboard')}</Link>

        {error && <Alert variant="danger" className="my-4">{error}</Alert>}

        {team && (
          <>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mt-4 mb-6">
              <div>
                <h1 className="text-2xl font-extrabold text-primary-navy">{team.name}</h1>
                {problem ? (
                  <Link to={`/problems/${team.problem_id}`} className="text-sm text-primary hover:underline">
                    {problem.title}
                  </Link>
                ) : (
                  <p className="text-sm text-ink-muted">{t('Problem: {{id}}', { id: team.problem_id })}</p>
                )}
              </div>
              <Link to={`/university/proposals/new?teamId=${team.id}&problemId=${team.problem_id}`}>
                <Button>{t('New Proposal')}</Button>
              </Link>
            </div>

            <h2 className="text-lg font-bold text-primary-navy mb-3">{t('Members')}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {(team.members || []).map((m) => (
                <Card key={m.id}>
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <p className="font-semibold text-primary-navy">{m.name || m.email}</p>
                      <p className="text-xs text-ink-muted">{m.email}</p>
                    </div>
                    <Badge role={m.role} />
                  </div>
                </Card>
              ))}
              {(!team.members || team.members.length === 0) && (
                <Card className="text-center py-8 text-ink-soft">{t('No members yet.')}</Card>
              )}
            </div>

            <Card>
              <h3 className="font-bold text-primary-navy mb-3">{t('Invite Collaborators')}</h3>
              <p className="text-xs text-ink-muted mb-3">
                {t('Search by name or email to invite registered students/faculty to your team.')}
              </p>
              <div className="flex items-center gap-3">
                <div className="flex-1 relative">
                  <Input
                    label={t('Search collaborators')}
                    value={query}
                    onChange={(e) => onSearch(e.target.value)}
                    placeholder={t('Name or email…')}
                  />
                  {searching && <p className="text-xs text-ink-muted mt-1">{t('Searching…')}</p>}
                  {results.length > 0 && (
                    <div className="absolute z-20 mt-1 w-full max-h-64 overflow-auto rounded-btn border border-line bg-white shadow-lg">
                      {results.map((u) => (
                        <div key={u.id} className="flex items-center justify-between gap-2 px-3 py-2 hover:bg-bg-soft border-b border-line last:border-0">
                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-primary-navy truncate">{u.name}</p>
                            <p className="text-xs text-ink-muted truncate">{u.email} · {t(u.role.replace('_', ' '))}</p>
                          </div>
                          <Button size="sm" onClick={() => handleAddUser(u.id)} loading={adding}>{t('Add')}</Button>
                        </div>
                      ))}
                    </div>
                  )}
                  {query.trim().length >= 2 && !searching && results.length === 0 && (
                    <p className="text-xs text-ink-muted mt-1">{t('No matches. Try inviting by email below.')}</p>
                  )}
                </div>
              </div>

              <form onSubmit={handleAddByEmail} className="flex flex-col sm:flex-row items-end gap-3 mt-4">
                <div className="sm:flex-1 w-full">
                  <Input
                    label={t('Invite by email')}
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={t('teammate@college.edu')}
                  />
                </div>
                <Button type="submit" loading={adding} disabled={!email.trim()}>{t('Add by Email')}</Button>
              </form>
            </Card>
          </>
        )}
      </main>
    </div>
  );
}

function Badge({ role }) {
  return <StatusBadge status={role || 'member'} size="sm" />;
}