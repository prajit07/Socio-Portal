import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { homeForRole } from '../lib/routes';
import { authApi, industriesApi } from '../api/client';
import { Button, Input, Select, Alert, Card } from '../components/ui';
import DomainMultiSelect from '../components/DomainMultiSelect';
import InstitutionSelect from '../components/InstitutionSelect';
import { useTranslation } from 'react-i18next';

const INDUSTRY_TYPES = [
  { value: 'startup', label: 'Startup' },
  { value: 'msme', label: 'MSME' },
  { value: 'corporate', label: 'Corporate' },
  { value: 'csr', label: 'CSR Arm' },
  { value: 'research_institution', label: 'Research Institution' },
  { value: 'innovation_hub', label: 'Innovation Hub' },
  { value: 'ngo', label: 'NGO' },
];

const ROLE_OPTIONS = [
  { value: 'citizen', title: 'Citizen', desc: 'Report problems in your community.' },
  { value: 'student', title: 'Student', desc: 'Join via your institution (dept & roll no).' },
  { value: 'university_admin', title: 'University', desc: 'Register your institution & mentor teams.' },
  { value: 'industry', title: 'Industry / Startup', desc: 'Discover & fund solutions.' },
  { value: 'government', title: 'Government', desc: 'Oversee impact & analytics.' },
];

export default function Register() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [role, setRole] = useState('citizen');
  const [form, setForm] = useState({ name: '', email: '', password: '', phone: '', company_name: '', industry_type: 'startup', domain_tags: [], university_id: '', university_label: '', department: '', roll_number: '' });
  const [step, setStep] = useState('form'); // 'form' | 'otp'
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [otp, setOtp] = useState('');
  const [devCode, setDevCode] = useState('');
  const [otpLoading, setOtpLoading] = useState(false);
  const [otpError, setOtpError] = useState('');

  const update = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const requestCode = async (email, purpose = 'register') => {
    try {
      const res = await authApi.requestOtp(email, purpose);
      setDevCode(res.data.dev_code || '');
      return res.data;
    } catch {
      // non-fatal; user will still get the email if SMTP is configured
      return null;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const payload = {
        name: form.name,
        email: form.email,
        password: form.password,
        role,
        phone: form.phone || undefined,
        university_id: role === 'student' && form.university_id ? form.university_id : undefined,
        department: role === 'student' ? form.department || undefined : undefined,
        roll_number: role === 'student' ? form.roll_number || undefined : undefined,
        domain_tags:
          role === 'industry' && form.domain_tags
            ? form.domain_tags.split(',').map((s) => s.trim()).filter(Boolean)
            : undefined,
      };
      await authApi.register(payload);
      const rc = await requestCode(form.email, 'register');
      console.log('[OTP DEBUG] request-code ->', rc);
      setStep('otp');
    } catch (err) {
      setError(err.response?.data?.detail || t('Registration failed. Email may already be used.'));
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setOtpError('');
    setOtpLoading(true);
    console.log('[OTP DEBUG] verify submit ->', { email: form.email, code: otp });
    try {
      await authApi.verifyOtp(form.email, otp, 'register');
      await login(form.email, form.password);
      if (role === 'industry' && form.company_name.trim() && form.domain_tags.length > 0) {
        try {
          await industriesApi.create({
            name: form.company_name.trim(),
            type: form.industry_type,
            domain_tags: form.domain_tags,
          });
        } catch {
          // profile creation is best-effort; user can finish it in Settings
        }
      }
      navigate(homeForRole(role));
    } catch (err) {
      console.warn('[OTP DEBUG] verify failed ->', err.response?.data);
      setOtpError(err.response?.data?.detail || t('Invalid or expired code.'));
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
        <Link to="/login" className="text-sm font-semibold text-primary hover:text-primary-dark">
          {t('Sign In')}
        </Link>
      </div>

      <div className="flex flex-1 items-start justify-center px-4 py-12">
        <Card className="w-full max-w-xl">
          {step === 'form' ? (
            <>
              <div className="mb-6">
                <h1 className="text-2xl font-extrabold text-primary-navy">{t('Create Account')}</h1>
                <p className="mt-1 text-sm text-ink-soft">{t('Join as the actor you represent.')}</p>
              </div>

              {error && <Alert variant="danger" className="mb-4">{error}</Alert>}

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-ink mb-2">{t('I am a')}</label>
                  <div className="grid grid-cols-2 gap-3">
                    {ROLE_OPTIONS.map((r) => (
                      <button
                        type="button"
                        key={r.value}
                        onClick={() => setRole(r.value)}
                        className={`text-left rounded-card border p-4 transition-colors ${
                          role === r.value
                            ? 'border-primary bg-bg-soft ring-1 ring-primary'
                            : 'border-line hover:border-primary'
                        }`}
                      >
                        <div className={`font-bold text-sm ${role === r.value ? 'text-primary' : 'text-primary-navy'}`}>
                          {t(r.title)}
                        </div>
                        <div className="mt-1 text-xs text-ink-soft">{t(r.desc)}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <Input
                    label={t("Full Name")}
                    required
                    value={form.name}
                    onChange={update('name')}
                    placeholder={t("John Doe")}
                  />
                  <Input
                    label={t("Email")}
                    type="email"
                    required
                    value={form.email}
                    onChange={update('email')}
                    placeholder={t("Enter your email")}
                  />
                  <Input 
                    label={t("Password")} 
                    type="password" 
                    name="password" 
                    value={form.password} 
                    onChange={update('password')}
                    hint={t("At least 8 characters.")} 
                    required 
                    minLength={8} 
                  />
                  <Input 
                    label={t("Phone (optional)")} 
                    name="phone" 
                    value={form.phone} 
                    onChange={update('phone')} 
                  />
                </div>
                
                {role === 'industry' && (
                  <div className="space-y-4">
                    <Input
                      label={t("Organisation Name")}
                      name="company_name"
                      value={form.company_name}
                      onChange={update('company_name')}
                      placeholder="e.g. Acme CleanTech"
                      required
                    />
                    <Select
                      label={t("Industry Type")}
                      name="industry_type"
                      value={form.industry_type}
                      onChange={update('industry_type')}
                      options={INDUSTRY_TYPES.map(it => ({ ...it, label: t(it.label) }))}
                    />
                    <DomainMultiSelect
                      label={t("Domain Expertise (comma separated)")}
                      value={form.domain_tags}
                      onChange={(tags) => setForm({ ...form, domain_tags: tags })}
                      placeholder={t("e.g. education, healthcare, infrastructure")}
                    />
                  </div>
                )}

                {role === 'student' && (
                  <div className="space-y-4">
                    <InstitutionSelect
                      label={t("Institution")}
                      required
                      value={{ id: form.university_id, label: form.university_label }}
                      onChange={(val) => setForm({ ...form, university_id: val?.id || '', university_label: val?.label || '' })}
                      placeholder={t("Select Institution")}
                    />
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <Input label={t("Department")} name="department" value={form.department} onChange={update('department')} placeholder={t("e.g. Computer Science")} required />
                      <Input label={t("Roll Number")} name="roll_number" value={form.roll_number} onChange={update('roll_number')} required />
                    </div>
                  </div>
                )}

                <Button type="submit" size="lg" loading={loading} className="w-full">
                  {t('Create Account')}
                </Button>
              </form>

              <p className="mt-6 text-center text-sm text-ink-soft">
                {t('Already have an account?')} {' '}
                <Link to="/login" className="font-semibold text-primary hover:underline">
                  {t('Sign In')}
                </Link>
              </p>
            </>
          ) : (
            <>
              <div className="mb-6">
                <h1 className="text-2xl font-extrabold text-primary-navy">{t('Verify your email')}</h1>
                <p className="mt-1 text-sm text-ink-soft">
                  {t('We sent a 6-digit code to')} <span className="font-semibold text-ink">{form.email}</span>.
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
                  name="otp"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder={t("6-digit code")}
                  inputMode="numeric"
                  required
                />
                <Button type="submit" size="lg" loading={otpLoading} className="w-full">
                  {t('Verify & Sign In')}
                </Button>
              </form>

              <div className="mt-6 text-center text-sm">
                <span className="text-ink-soft">{t("Didn't receive a code?")} </span>
                <button
                  type="button"
                  className="font-semibold text-primary hover:underline"
                  onClick={async () => {
                    await requestCode(form.email, 'register');
                  }}
                >
                  {t('Resend')}
                </button>
              </div>

              <div className="mt-4 text-center">
                <button type="button" className="text-ink-muted hover:underline" onClick={() => setStep('form')}>
                  Back
                </button>
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
