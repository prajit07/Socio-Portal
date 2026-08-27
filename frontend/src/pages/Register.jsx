import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { homeForRole } from '../lib/routes';
import { Button, Input, Alert, Card } from '../components/ui';

const ROLE_OPTIONS = [
  { value: 'citizen', title: 'Citizen', desc: 'Report problems in your community.' },
  { value: 'university_admin', title: 'University', desc: 'Register your institution & mentor teams.' },
  { value: 'industry', title: 'Industry / Startup', desc: 'Discover & fund solutions.' },
  { value: 'government', title: 'Government', desc: 'Oversee impact & analytics.' },
];

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [role, setRole] = useState('citizen');
  const [form, setForm] = useState({ name: '', email: '', password: '', phone: '', domain_tags: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const update = (k) => (e) => setForm({ ...form, [k]: e.target.value });

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
        domain_tags:
          role === 'industry' && form.domain_tags
            ? form.domain_tags.split(',').map((s) => s.trim()).filter(Boolean)
            : undefined,
      };
      await register(payload);
      const stored = JSON.parse(localStorage.getItem('user') || '{}');
      navigate(homeForRole(stored.role));
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Email may already be used.');
    } finally {
      setLoading(false);
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
          <span className="text-lg font-extrabold text-primary-navy">InnoSphere</span>
        </Link>
        <Link to="/login" className="text-sm font-semibold text-primary hover:text-primary-dark">
          Sign in
        </Link>
      </div>

      <div className="flex flex-1 items-start justify-center px-4 py-12">
        <Card className="w-full max-w-xl">
          <div className="mb-6">
            <h1 className="text-2xl font-extrabold text-primary-navy">Create your account</h1>
            <p className="mt-1 text-sm text-ink-soft">Join as the actor you represent.</p>
          </div>

          {error && <Alert variant="danger" className="mb-4">{error}</Alert>}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-ink mb-2">I am a</label>
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
                    <div className="font-bold text-primary-navy">{r.title}</div>
                    <div className="text-xs text-ink-soft mt-1">{r.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input label="Full name" name="name" value={form.name} onChange={update('name')} required />
              <Input label="Phone (optional)" name="phone" value={form.phone} onChange={update('phone')} />
            </div>
            <Input label="Email" type="email" name="email" value={form.email} onChange={update('email')} required />
            <Input label="Password" type="password" name="password" value={form.password} onChange={update('password')}
              hint="At least 8 characters." required minLength={8} />
            {role === 'industry' && (
              <Input
                label="Domain tags (optional, comma separated)"
                name="domain_tags"
                value={form.domain_tags}
                onChange={update('domain_tags')}
                placeholder="water_sanitation, waste_management"
                hint="Leave blank to receive all problems."
              />
            )}

            <Button type="submit" size="lg" loading={loading} className="w-full">
              Create Account
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-ink-muted">
            Already registered?{' '}
            <Link to="/login" className="font-semibold text-primary hover:underline">Sign in</Link>
          </p>
        </Card>
      </div>
    </div>
  );
}
