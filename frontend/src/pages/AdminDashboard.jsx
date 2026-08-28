import { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { adminApi } from '../api/client';
import { Button, Card, Input, TextArea, Select, StatusBadge, RoleBadge, Alert, PageLoader } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);
const ROLES = ['citizen', 'student', 'faculty', 'university_admin', 'industry', 'government', 'admin'];

export default function AdminDashboard() {
  const { user } = useAuth();
  const [tab, setTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [mod, setMod] = useState([]);
  const [cfg, setCfg] = useState(null);
  const [msg, setMsg] = useState('');
  const [bRole, setBRole] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [u, m, c] = await Promise.all([adminApi.users(), adminApi.moderation(), adminApi.aiConfig()]);
      setUsers(asData(u) || []);
      setMod(asData(m) || []);
      setCfg(asData(c));
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load admin data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const setUserRole = async (uid, role) => {
    setBusy(true);
    try { await adminApi.updateUser(uid, { role }); await load(); setError(''); }
    catch (e) { setError(e.response?.data?.detail || 'Failed to update user.'); }
    finally { setBusy(false); }
  };

  const toggleVerified = async (u) => {
    setBusy(true);
    try { await adminApi.updateUser(u.id, { is_email_verified: !u.is_email_verified }); await load(); setError(''); }
    catch (e) { setError(e.response?.data?.detail || 'Failed to update user.'); }
    finally { setBusy(false); }
  };

  const setProblemStatus = async (pid, status) => {
    setBusy(true);
    try { await adminApi.setStatus(pid, { status }); await load(); setError(''); }
    catch (e) { setError(e.response?.data?.detail || 'Failed to update status.'); }
    finally { setBusy(false); }
  };

  const broadcast = async (e) => {
    e.preventDefault();
    if (!msg.trim()) return;
    setBusy(true);
    try { await adminApi.broadcast({ message: msg, role: bRole || undefined }); setMsg(''); setError(''); }
    catch (e) { setError(e.response?.data?.detail || 'Failed to broadcast.'); }
    finally { setBusy(false); }
  };

  if (user?.role !== 'admin') return <PageLoader />;
  if (loading) return <PageLoader />;

  const tabs = [
    { id: 'users', label: 'Users' },
    { id: 'moderation', label: 'Moderation' },
    { id: 'ai', label: 'AI Config' },
    { id: 'broadcast', label: 'Broadcast' },
  ];

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-extrabold text-primary-navy mb-6">Admin Console</h1>
        {error && <Alert variant="danger" className="mb-6">{error}</Alert>}

        <div className="flex flex-wrap gap-2 mb-6">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-btn text-sm font-semibold transition ${tab === t.id ? 'bg-primary text-white' : 'bg-white text-ink-soft border border-line'}`}
            >
              {t.label}
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
                        <span className="text-xs text-tag-success font-semibold">verified</span>
                      ) : (
                        <span className="text-xs text-tag-danger font-semibold">unverified</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Select
                      value={u.role}
                      onChange={(e) => setUserRole(u.id, e.target.value)}
                      options={ROLES.map((r) => ({ value: r, label: r.replace('_', ' ') }))}
                      className="w-44"
                    />
                    <Button size="sm" variant="secondary" loading={busy} onClick={() => toggleVerified(u)}>
                      {u.is_email_verified ? 'Unverify' : 'Verify'}
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
                    <p className="text-xs text-ink-muted">{p.ai_category} · {p.status}{p.ai_duplicate_of ? ` · dup of ${p.ai_duplicate_of}` : ''}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Select
                      value={p.status}
                      onChange={(e) => setProblemStatus(p.id, e.target.value)}
                      options={['open', 'under_review', 'in_progress', 'implemented', 'duplicate', 'closed', 'rejected'].map((s) => ({ value: s, label: s.replace('_', ' ') }))}
                      className="w-40"
                    />
                  </div>
                </div>
              ))}
              {mod.length === 0 && <p className="text-ink-soft">No problems to moderate.</p>}
            </div>
          </Card>
        )}

        {tab === 'ai' && (
          <Card className="max-w-xl">
            <h2 className="font-bold text-primary-navy mb-3">AI Pipeline Configuration</h2>
            <div className="space-y-2 text-sm">
              <p><span className="font-semibold">AI enabled:</span> {cfg?.ai_enabled ? 'Yes' : 'No'}</p>
              <p><span className="font-semibold">Duplicate threshold:</span> {cfg?.duplicate_threshold}</p>
              <p><span className="font-semibold">Email configured:</span> {cfg?.email_configured ? 'Yes' : 'No'}</p>
              <p className="text-ink-muted mt-2">Set CLOUDFLARE_* keys and EMAIL_* keys in the backend .env to enable AI tagging, duplicate detection and OTP email.</p>
            </div>
          </Card>
        )}

        {tab === 'broadcast' && (
          <Card className="max-w-xl">
            <h2 className="font-bold text-primary-navy mb-3">Broadcast Notification</h2>
            <form onSubmit={broadcast} className="space-y-3">
              <TextArea label="Message" rows={4} value={msg} onChange={(e) => setMsg(e.target.value)} placeholder="Announcement text..." required />
              <Select
                label="Target role (optional)"
                value={bRole}
                onChange={(e) => setBRole(e.target.value)}
                options={[{ value: '', label: 'All users' }, ...ROLES.map((r) => ({ value: r, label: r.replace('_', ' ') }))]}
              />
              <Button type="submit" size="sm" loading={busy}>Send Broadcast</Button>
            </form>
          </Card>
        )}
      </main>
    </div>
  );
}
