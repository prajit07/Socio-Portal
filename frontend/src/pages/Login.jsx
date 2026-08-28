import { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { homeForRole } from '../lib/routes';
import { authApi } from '../api/client';
import { Button, Input, Alert, Card } from '../components/ui';
import { useTranslation } from 'react-i18next';

export default function Login() {
  const { t } = useTranslation();
  const { loginWithOtp } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [step, setStep] = useState('credentials'); // 'credentials' | 'otp'
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [otp, setOtp] = useState('');
  const [devCode, setDevCode] = useState('');
  const [otpError, setOtpError] = useState('');
  const [otpLoading, setOtpLoading] = useState(false);
  const requestingRef = useRef(false);

  const handleCredentials = async (e) => {
    e.preventDefault();
    if (requestingRef.current) return; // guard against double-submit (stale code)
    requestingRef.current = true;
    setError('');
    setLoading(true);
    try {
      const res = await authApi.loginRequestCode(email, password);
      console.log('[OTP DEBUG] request-code ->', res.data);
      setDevCode(res.data.dev_code || '');
      setStep('otp');
    } catch (err) {
      setError(err.response?.data?.detail || t('Invalid email or password.'));
    } finally {
      setLoading(false);
      requestingRef.current = false;
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setOtpError('');
    setOtpLoading(true);
    console.log('[OTP DEBUG] verify submit ->', { email, code: otp });
    try {
      await loginWithOtp(email, otp);
      const stored = JSON.parse(localStorage.getItem('user') || '{}');
      navigate(homeForRole(stored.role));
    } catch (err) {
      console.warn('[OTP DEBUG] verify failed ->', {
        message: err?.message,
        code: err?.code,
        status: err?.response?.status,
        data: err?.response?.data,
        url: err?.config?.url,
      });
      setOtp('');
      const detail = err?.response?.data?.detail;
      setOtpError(
        detail ||
          (err?.response
            ? t('Invalid or expired code. Click Resend to get a new one.')
            : t('Cannot reach the server. Is the backend running on :8000? Check the Network tab for a CORS/connection error.'))
      );
    } finally {
      setOtpLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-soft flex flex-col">
      <div className="flex items-center justify-between px-6 h-[72px] border-b border-line bg-white">
        <Link to="/" className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-btn bg-primary text-white">
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z" />
            </svg>
          </span>
          <span className="text-lg font-extrabold text-primary-navy">Socio Connect</span>
        </Link>
        <Link to="/register" className="text-sm font-semibold text-primary hover:text-primary-dark">
          {t('Create account')}
        </Link>
      </div>

      <div className="flex flex-1 items-center justify-center px-4 py-12">
        <Card className="w-full max-w-md">
          {step === 'credentials' ? (
            <>
              <div className="mb-6">
                <h1 className="text-2xl font-extrabold text-primary-navy">{t('Welcome back')}</h1>
                <p className="mt-1 text-sm text-ink-soft">{t('Sign in to continue to your portal.')}</p>
              </div>

              {error && <Alert variant="danger" className="mb-4">{error}</Alert>}

              <form onSubmit={handleCredentials} className="space-y-4">
                <Input
                  label={t("Email")}
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t("Enter your email")}
                />
                <Input
                  label={t("Password")}
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t("Enter your password")}
                />
                <Button type="submit" className="w-full" size="lg" loading={loading} disabled={loading}>
                  {t('Continue')}
                </Button>
              </form>

              <p className="mt-6 text-center text-sm text-ink-muted">
                {t('New here?')} {' '}
                <Link to="/register" className="font-semibold text-primary hover:underline">
                  {t('Create an account')}
                </Link>
              </p>
            </>
          ) : (
            <>
              <div className="mb-6">
                <h1 className="text-2xl font-extrabold text-primary-navy">{t('Two-Step Verification')}</h1>
                <p className="mt-1 text-sm text-ink-soft">
                  {t('We sent a 6-digit code to')} <span className="font-semibold text-ink">{email}</span>.
                </p>
              </div>

              {otpError && <Alert variant="danger" className="mb-4">{otpError}</Alert>}

              {devCode && (
                <Alert variant="info" className="mb-4 text-xs font-mono">
                  {t('DEV MODE: Use this code:')} <span className="font-bold text-primary">{devCode}</span>
                </Alert>
              )}

              <form onSubmit={handleVerify} className="space-y-4">
                <Input
                  label={t("Verification Code")}
                  required
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  placeholder={t("6-digit code")}
                  maxLength={6}
                  className="text-center text-xl tracking-widest"
                  autoFocus
                />
                <Button type="submit" className="w-full" size="lg" loading={otpLoading} disabled={otpLoading || otp.length !== 6}>
                  {t('Verify & Sign In')}
                </Button>
              </form>

              <div className="mt-6 text-center text-sm text-ink-soft">
                {t("Didn't receive a code?")}{' '}
                <button
                  type="button"
                  onClick={async () => {
                    try {
                      const res = await authApi.loginRequestCode(email, password);
                      setDevCode(res.data.dev_code || '');
                    } catch {
                      /* ignore */
                    }
                  }}
                  className="font-bold text-primary hover:text-primary-dark"
                >
                  {t('Resend')}
                </button>
              </div>

              <div className="mt-4 text-center">
                <button type="button" className="text-ink-muted hover:underline" onClick={() => setStep('credentials')}>
                  {t('Back')}
                </button>
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
