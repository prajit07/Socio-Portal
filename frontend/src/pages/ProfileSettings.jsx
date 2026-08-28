import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/client';
import { Card, Button, Alert, ConfirmDialog, RoleBadge } from '../components/ui';

const roleLabels = {
  citizen: 'Citizen',
  student: 'Student',
  faculty: 'Faculty Mentor',
  university_admin: 'University',
  industry: 'Industry',
  government: 'Government',
  admin: 'Admin',
};

export default function ProfileSettings() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleDelete = async () => {
    setBusy(true);
    setError('');
    try {
      await authApi.deleteAccount();
      logout();
      navigate('/');
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to delete account.');
      setConfirmOpen(false);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-extrabold text-primary-navy">Profile & Settings</h1>
        <p className="text-ink-soft mt-1">Manage your account details and preferences.</p>

        <Card className="mt-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-lg font-bold text-primary-navy">{user?.name}</p>
              <p className="text-sm text-ink-muted">{user?.email}</p>
            </div>
            <div className="flex items-center gap-2">
              <RoleBadge role={user?.role} />
              {user?.is_email_verified ? (
                <span className="text-xs text-tag-success font-semibold">verified</span>
              ) : (
                <span className="text-xs text-tag-danger font-semibold">unverified</span>
              )}
            </div>
          </div>
          <p className="text-sm text-ink-soft mt-3">
            Role: <span className="font-semibold text-primary-navy">{roleLabels[user?.role] || user?.role}</span>
          </p>
        </Card>

        <Card className="mt-6 border-tag-danger/40">
          <h2 className="font-bold text-tag-danger mb-1">Danger Zone</h2>
          <p className="text-sm text-ink-soft mb-4">
            Deleting your account permanently removes your personal data (comments, upvotes, memberships,
            notifications). Problems, solutions and teams you created will be kept but disassociated from your account.
          </p>
          <Button variant="danger" onClick={() => setConfirmOpen(true)}>Delete Account</Button>
        </Card>

        {error && <Alert variant="danger" className="mt-6">{error}</Alert>}

        <ConfirmDialog
          open={confirmOpen}
          title="Delete your account?"
          message="This action cannot be undone. Your personal data will be removed immediately."
          confirmLabel="Delete Account"
          danger
          onCancel={() => setConfirmOpen(false)}
          onConfirm={handleDelete}
        />
      </main>
    </div>
  );
}
