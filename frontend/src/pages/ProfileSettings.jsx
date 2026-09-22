import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/client';
import { Card, Button, Alert, ConfirmDialog, Input, Modal, RoleBadge } from '../components/ui';
import { useTranslation } from 'react-i18next';

export default function ProfileSettings() {
  const { t } = useTranslation();
  const { user, logout, setUser } = useAuth();
  const navigate = useNavigate();
  const roleLabels = {
    citizen: t('Citizen'),
    student: t('Student'),
    faculty: t('Faculty Mentor'),
    university_admin: t('University'),
    industry: t('Industry'),
    government: t('Government'),
    admin: t('Admin'),
  };
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  // profile edit
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(user?.name || '');
  const [phone, setPhone] = useState(user?.phone || '');

  // password reset modal
  const [pwOpen, setPwOpen] = useState(false);
  const [pwStep, setPwStep] = useState('send');
  const [pwCode, setPwCode] = useState('');
  const [pwNew, setPwNew] = useState('');
  const [pwConfirm, setPwConfirm] = useState('');
  const [pwBusy, setPwBusy] = useState(false);
  const [pwDev, setPwDev] = useState('');

  // email verification modal
  const [verifyOpen, setVerifyOpen] = useState(false);
  const [vCode, setVCode] = useState('');
  const [vBusy, setVBusy] = useState(false);
  const [vDev, setVDev] = useState('');

  const flashErr = (m) => { setError(m); setSuccess(''); };
  const flashOk = (m) => { setSuccess(m); setError(''); };

  const saveProfile = async () => {
    setBusy(true);
    setError('');
    try {
      const res = await authApi.updateProfile({ name, phone: phone || null });
      const updated = res.data;
      setUser(updated);
      localStorage.setItem('user', JSON.stringify(updated));
      setEditing(false);
      flashOk(t('Profile updated.'));
    } catch (e) {
      flashErr(e.response?.data?.detail || t('Failed to update profile.'));
    } finally {
      setBusy(false);
    }
  };

  const sendPwOtp = async () => {
    setPwBusy(true);
    setError('');
    try {
      const res = await authApi.requestOtp(user.email, 'reset');
      setPwDev(res.data?.dev_code || '');
      setPwStep('reset');
      flashOk(t('OTP sent to your email.'));
    } catch {
      flashErr(t('Could not send OTP. Try again.'));
    } finally {
      setPwBusy(false);
    }
  };

  const doReset = async () => {
    if (pwNew.length < 8) { flashErr(t('Password must be at least 8 characters.')); return; }
    if (pwNew !== pwConfirm) { flashErr(t('Passwords do not match.')); return; }
    setPwBusy(true);
    setError('');
    try {
      await authApi.resetPassword({ email: user.email, code: pwCode, new_password: pwNew });
      setPwOpen(false);
      setPwStep('send');
      setPwCode(''); setPwNew(''); setPwConfirm(''); setPwDev('');
      flashOk(t('Password changed successfully.'));
    } catch (e) {
      flashErr(e.response?.data?.detail || t('Failed to reset password.'));
    } finally {
      setPwBusy(false);
    }
  };

  const sendVerifyOtp = async () => {
    setVBusy(true);
    setError('');
    try {
      const res = await authApi.requestOtp(user.email, 'verify');
      setVDev(res.data?.dev_code || '');
      flashOk(t('Verification OTP sent.'));
    } catch {
      flashErr(t('Could not send OTP.'));
    } finally {
      setVBusy(false);
    }
  };

  const doVerify = async () => {
    setVBusy(true);
    setError('');
    try {
      await authApi.verifyOtp(user.email, vCode, 'verify');
      const me = (await authApi.me()).data;
      setUser(me);
      localStorage.setItem('user', JSON.stringify(me));
      setVerifyOpen(false);
      setVCode('');
      flashOk(t('Email verified.'));
    } catch (e) {
      flashErr(e.response?.data?.detail || t('Invalid or expired code.'));
    } finally {
      setVBusy(false);
    }
  };

  const handleDelete = async () => {
    setBusy(true);
    setError('');
    try {
      await authApi.deleteAccount();
      logout();
      navigate('/');
    } catch (e) {
      flashErr(e.response?.data?.detail || t('Failed to delete account.'));
      setConfirmOpen(false);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-extrabold text-primary-navy">{t('Profile & Settings')}</h1>
        <p className="text-ink-soft mt-1">{t('Manage your account details and security.')}</p>

        {error && <Alert variant="danger" className="mt-6">{error}</Alert>}
        {success && <Alert variant="success" className="mt-6">{success}</Alert>}

        {/* Profile */}
        <Card className="mt-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-lg font-bold text-primary-navy">{user?.name}</p>
              <p className="text-sm text-ink-muted">{user?.email}</p>
            </div>
            <div className="flex items-center gap-2">
              <RoleBadge role={user?.role} />
              {user?.is_email_verified ? (
                <span className="text-xs text-tag-success font-semibold">{t('verified')}</span>
              ) : (
                <span className="text-xs text-tag-danger font-semibold">{t('unverified')}</span>
              )}
            </div>
          </div>

          {!editing ? (
            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-ink-soft">
                <span className="font-semibold text-primary-navy">{roleLabels[user?.role] || user?.role}</span>
                {user?.phone && <span className="ml-2">· {user.phone}</span>}
              </div>
              <Button size="sm" variant="secondary" onClick={() => { setName(user?.name || ''); setPhone(user?.phone || ''); setEditing(true); }}>
                {t('Edit Profile')}
              </Button>
            </div>
          ) : (
            <div className="mt-4 space-y-3">
              <Input label={t('Full name')} value={name} onChange={(e) => setName(e.target.value)} />
              <Input label={t('Phone')} value={phone} onChange={(e) => setPhone(e.target.value)} />
              <div className="flex gap-2">
                <Button size="sm" onClick={saveProfile} loading={busy}>{t('Save')}</Button>
                <Button size="sm" variant="secondary" onClick={() => setEditing(false)}>{t('Cancel')}</Button>
              </div>
            </div>
          )}
        </Card>

        {/* Security */}
        <Card className="mt-6">
          <h2 className="font-bold text-primary-navy mb-3">{t('Security')}</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-ink">{t('Password')}</p>
                <p className="text-xs text-ink-muted">{t("Change your password. We'll verify it with an email OTP.")}</p>
              </div>
              <Button size="sm" variant="secondary" onClick={() => { setPwOpen(true); setPwStep('send'); setPwDev(''); }}>
                {t('Change Password')}
              </Button>
            </div>
            {!user?.is_email_verified && (
              <div className="flex items-center justify-between gap-4 border-t border-line pt-3">
                <div>
                  <p className="text-sm font-semibold text-ink">{t('Email verification')}</p>
                  <p className="text-xs text-ink-muted">{t('Verify your email to unlock all features.')}</p>
                </div>
                <Button size="sm" variant="secondary" onClick={() => { setVerifyOpen(true); setVDev(''); }}>
                  {t('Verify Email')}
                </Button>
              </div>
            )}
          </div>
        </Card>

        {/* Danger zone */}
        <Card className="mt-6 border-tag-danger/40">
          <h2 className="font-bold text-tag-danger mb-1">{t('Danger Zone')}</h2>
          <p className="text-sm text-ink-soft mb-4">
            {t('Deleting your account permanently removes your personal data (comments, upvotes, memberships, notifications). Problems, solutions and teams you created will be kept but disassociated from your account.')}
          </p>
          <Button variant="danger" onClick={() => setConfirmOpen(true)}>{t('Delete Account')}</Button>
        </Card>
      </main>

      {/* Password reset modal */}
      <Modal open={pwOpen} onClose={() => setPwOpen(false)} title={t('Change Password')}>
        {pwStep === 'send' ? (
          <div className="space-y-4">
            <p className="text-sm text-ink-soft">
              {t("We'll send a one-time code to")} <span className="font-semibold">{user?.email}</span> {t("to verify it's you.")}
            </p>
            <Button onClick={sendPwOtp} loading={pwBusy} className="w-full">{t('Send OTP')}</Button>
          </div>
        ) : (
          <div className="space-y-4">
            <Input
              label={t('OTP code')}
              value={pwCode}
              onChange={(e) => setPwCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder={t('6-digit code')}
              inputMode="numeric"
            />
            <Input label={t('New password')} type="password" value={pwNew} onChange={(e) => setPwNew(e.target.value)} hint={t('At least 8 characters.')} />
            <Input label={t('Confirm new password')} type="password" value={pwConfirm} onChange={(e) => setPwConfirm(e.target.value)} />
            {pwDev && (
              <p className="text-xs text-ink-muted">{t('Dev OTP:')} <span className="font-mono font-semibold text-primary">{pwDev}</span></p>
            )}
            <div className="flex gap-2">
              <Button onClick={doReset} loading={pwBusy} className="flex-1">{t('Reset Password')}</Button>
              <Button variant="secondary" onClick={() => { setPwStep('send'); setPwCode(''); }}>{t('Back')}</Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Email verification modal */}
      <Modal open={verifyOpen} onClose={() => setVerifyOpen(false)} title={t('Verify Email')}>
        <div className="space-y-4">
          <p className="text-sm text-ink-soft">
            {t('Enter the 6-digit code we sent to')} <span className="font-semibold">{user?.email}</span>.
          </p>
          <Input
            label={t('OTP code')}
            value={vCode}
            onChange={(e) => setVCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            placeholder={t('6-digit code')}
            inputMode="numeric"
          />
          {vDev && (
            <p className="text-xs text-ink-muted">{t('Dev OTP:')} <span className="font-mono font-semibold text-primary">{vDev}</span></p>
          )}
          <div className="flex gap-2">
            <Button onClick={doVerify} loading={vBusy} className="flex-1">{t('Verify')}</Button>
            <Button variant="secondary" onClick={sendVerifyOtp} loading={vBusy}>{t('Resend')}</Button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        open={confirmOpen}
        title={t('Delete your account?')}
        message={t('This action cannot be undone. Your personal data will be removed immediately.')}
        confirmLabel={t('Delete Account')}
        danger
        onCancel={() => setConfirmOpen(false)}
        onConfirm={handleDelete}
      />
    </div>
  );
}
