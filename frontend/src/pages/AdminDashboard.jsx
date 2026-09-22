import { useState, useEffect, useCallback } from 'react';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { adminApi } from '../api/client';
import { Button, Card, TextArea, Select, RoleBadge, Alert, PageLoader } from '../components/ui';
import { useTranslation } from 'react-i18next';

const asData = (r) => (r && r.data !== undefined ? r.data : r);
const ROLES = ['citizen', 'student', 'faculty', 'university_admin', 'industry', 'government', 'admin'];

export default function AdminDashboard() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [tab, setTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [mod, setMod] = useState([]);
  const [cfg, setCfg] = useState(null);
  const [msg, setMsg] = useState('');
  const [bRole, setBRole] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [u, m, c] = await Promise.all([adminApi.users(), adminApi.moderation(), adminApi.aiConfig()]);
      setUsers(asData(u) || []);
      setMod(asData(m) || []);
      setCfg(asData(c));
    } catch (e) {
      setError(e.response?.data?.detail || t('Failed to load admin data.'));
    } finally {
      setLoading(false);
    }
  }, []);

  // eslint-disable-next-line react/set-state-in-effect -- initial server data fetch on mount
  useEffect(() => { load(); }, [load]);

  const setUserRole = async (uid, role) => {
    setBusy(true);
    try { await adminApi.updateUser(uid, { role }); await load(); setError(''); }
    catch (e) { setError(e.response?.data?.detail || t('Failed to update user.')); }
    finally { setBusy(false); }
  };

  const toggleVerified = async (u) => {
    setBusy(true);
    try { await adminApi.updateUser(u.id, { is_email_verified: !u.is_email_verified }); await load(); setError(''); }
    catch (e) { setError(e.response?.data?.detail || t('Failed to update user.')); }
    finally { setBusy(false); }
  };

  const setProblemStatus = async (pid, status) => {
    setBusy(true);
    try { await adminApi.setStatus(pid, { status }); await load(); setError(''); }
    catch (e) { setError(e.response?.data?.detail || t('Failed to update status.')); }
    finally { setBusy(false); }
  };

  const broadcast = async (e) => {
    e.preventDefault();
    if (!msg.trim()) return;
    setBusy(true);
    try { await adminApi.broadcast({ message: msg, role: bRole || undefined }); setMsg(''); setError(''); }
    catch (e) { setError(e.response?.data?.detail || t('Failed to broadcast.')); }
    finally { setBusy(false); }
  };

  if (user?.role !== 'admin') return <PageLoader />;
  if (loading) return <PageLoader />;

  const tabs = [
    { id: 'users', label: t('Users') },
    { id: 'moderation', label: t('Moderation') },
    { id: 'ai', label: t('AI Config') },
    { id: 'broadcast', label: t('Broadcast') },
  ];

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-extrabold text-primary-navy mb-6">{t('Admin Console')}</h1>
        {error && <Alert variant="danger" className="mb-6">{error}</Alert>}

        <div className="flex flex-wrap gap-2 mb-6">
          {tabs.map((tb) => (
            <button
              key={tb.id}
              onClick={() => setTab(tb.id)}
              className={`px-4 py-2 rounded-btn text-sm font-semibold transition ${tab === tb.id ? 'bg-primary text-white' : 'bg-white text-ink-soft border border-line'}`}
            >
              {tb.label}
            </button>
          ))}
        </div>

        {tab === 'users' && (
          <Card>
            <div className="space-y-3">
              {users.map((u) => (
                <div key={u.id} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-line pb-3">
                  <div>
                    <p className="font-semibold text-primary-navy">{u.name} <span className="text-xs text-ink-muted">({u.email})</span></p>
                    <div className="flex items-center gap-2 mt-1">
                      <RoleBadge role={u.role} />
                      {u.is_email_verified ? (
                        <span className="text-xs text-tag-success font-semibold">{t('verified')}</span>
                      ) : (
                        <span className="text-xs text-tag-danger font-semibold">{t('unverified')}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Select
                      value={u.role}
                      onChange={(e) => setUserRole(u.id, e.target.value)}
                      options={ROLES.map((r) => ({ value: r, label: t(r.replace('_', ' ')) }))}
                      className="w-44"
                    />
                    <Button size="sm" variant="secondary" loading={busy} onClick={() => toggleVerified(u)}>
                      {u.is_email_verified ? t('Unverify') : t('Verify')}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {tab === 'moderation' && (
          <Card>
            <div className="space-y-3">
              {mod.map((p) => (
                <div key={p.id} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-line pb-3">
                  <div>
                    <p className="font-semibold text-primary-navy">{p.title}</p>
                    <p className="text-xs text-ink-muted">{t(p.ai_category)} · {p.status}{p.ai_duplicate_of ? ` · ${t('dup of {{id}}', { id: p.ai_duplicate_of })}` : ''}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Select
                      value={p.status}
                      onChange={(e) => setProblemStatus(p.id, e.target.value)}
                      options={['open', 'under_review', 'in_progress', 'implemented', 'duplicate', 'closed', 'rejected'].map((s) => ({ value: s, label: t(s.replace('_', ' ')) }))}
                      className="w-40"
                    />
                  </div>
                </div>
              ))}
              {mod.length === 0 && <p className="text-ink-soft">{t('No problems to moderate.')}</p>}
            </div>
          </Card>
        )}

        {tab === 'ai' && (
          <Card className="max-w-xl">
            <h2 className="font-bold text-primary-navy mb-3">{t('AI Pipeline Configuration')}</h2>
            <div className="space-y-2 text-sm">
              <p><span className="font-semibold">{t('AI enabled:')}</span> {cfg?.ai_enabled ? t('Yes') : t('No')}</p>
              <p><span className="font-semibold">{t('Duplicate threshold:')}</span> {cfg?.duplicate_threshold}</p>
              <p><span className="font-semibold">{t('Email configured:')}</span> {cfg?.email_configured ? t('Yes') : t('No')}</p>
              <p className="text-ink-muted mt-2">{t('Set CLOUDFLARE_* keys and EMAIL_* keys in the backend .env to enable AI tagging, duplicate detection and OTP email.')}</p>
            </div>
          </Card>
        )}

        {tab === 'broadcast' && (
          <Card className="max-w-xl">
            <h2 className="font-bold text-primary-navy mb-3">{t('Broadcast Notification')}</h2>
            <form onSubmit={broadcast} className="space-y-3">
              <TextArea label={t('Message')} rows={4} value={msg} onChange={(e) => setMsg(e.target.value)} placeholder={t('Announcement text...')} required />
              <Select
                label={t('Target role (optional)')}
                value={bRole}
                onChange={(e) => setBRole(e.target.value)}
                options={[{ value: '', label: t('All users') }, ...ROLES.map((r) => ({ value: r, label: t(r.replace('_', ' ')) }))]}
              />
              <Button type="submit" size="sm" loading={busy}>{t('Send Broadcast')}</Button>
            </form>
          </Card>
        )}
      </main>
    </div>
  );
}
