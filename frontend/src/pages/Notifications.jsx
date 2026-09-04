import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { notificationsApi } from '../api/client';
import { Button, Card, Alert, PageLoader } from '../components/ui';

export default function Notifications() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await notificationsApi.list();
      setItems(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load notifications.');
    } finally {
      setLoading(false);
    }
  }, []);

  // eslint-disable-next-line react/set-state-in-effect -- initial server data fetch on mount
  useEffect(() => { load(); }, [load]);

  const markRead = async (id) => {
    await notificationsApi.markRead(id);
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
  };

  const markAll = async () => {
    await notificationsApi.markAllRead();
    setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
  };

  const unread = items.filter((n) => !n.is_read).length;

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-extrabold text-primary-navy">Notifications</h1>
            <p className="text-ink-soft mt-1">{unread} unread</p>
          </div>
          {unread > 0 && <Button variant="secondary" size="sm" onClick={markAll}>Mark all read</Button>}
        </div>

        {error && <Alert variant="danger" className="mb-4">{error}</Alert>}
        {loading ? <PageLoader /> : items.length === 0 ? (
          <Card className="text-center py-12 text-ink-soft">You're all caught up.</Card>
        ) : (
          <div className="space-y-3">
            {items.map((n) => (
              <Card key={n.id} padding="sm" className={n.is_read ? 'opacity-70' : 'border-primary'}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <span className={`mt-1 h-2 w-2 rounded-full ${n.is_read ? 'bg-line' : 'bg-primary'}`} />
                    <div>
                      <p className="text-sm text-ink">{n.message}</p>
                      <p className="text-xs text-ink-muted mt-1">{new Date(n.created_at).toLocaleString()}</p>
                    </div>
                  </div>
                  {n.reference_id && (
                    <Link to={`/problems/${n.reference_id}`} className="text-xs font-semibold text-primary hover:underline">View</Link>
                  )}
                  {!n.is_read && (
                    <button onClick={() => markRead(n.id)} className="text-xs font-semibold text-ink-muted hover:text-primary hover:underline">Mark read</button>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
