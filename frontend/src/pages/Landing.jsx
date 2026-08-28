import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Hero from '../components/ui/Hero';
import { Card, Button, Badge } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { homeForRole } from '../lib/routes';

const steps = [
  {
    n: '01',
    title: 'Citizen reports a problem',
    body: 'Upload photos, video, voice or text with a location. No expertise needed — just describe what is wrong.',
  },
  {
    n: '02',
    title: 'AI validates & routes',
    body: 'Our pipeline categorizes, scores priority, detects duplicates and routes the problem to the right universities and industry partners.',
  },
  {
    n: '03',
    title: 'Solvers collaborate',
    body: 'University teams draft proposals; industry funds and co-develops through prototype, pilot and implementation.',
  },
  {
    n: '04',
    title: 'Government tracks impact',
    body: 'A live dashboard aggregates every stage — from report to measurable social impact.',
  },
];

const features = [
  { title: 'AI Categorization', body: 'Automatic tagging against a 12-domain taxonomy with confidence scores.' },
  { title: 'Smart Routing', body: 'Every HEI sees all problems; industry is matched by domain tags.' },
  { title: 'Duplicate Detection', body: 'Token-similarity checks flag repeats before they clutter the system.' },
  { title: 'Full Traceability', body: 'Status timelines from submission to implementation, visible to all actors.' },
];

export default function Landing() {
  const { user } = useAuth();
  const primary = user
    ? { to: homeForRole(user.role), label: 'Go to Dashboard' }
    : { to: '/register', label: 'Get Started' };
  const secondary = user ? { to: '/problems', label: 'Browse Problems' } : { to: '/login', label: 'Sign In' };
  const mapLink = { to: '/problems/map', label: 'View Public Map' };

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <Hero
        eyebrow="Societal Innovation Collaboration Portal"
        title="Turn community problems into"
        highlight="collective solutions"
        subtitle="A civic-tech platform where citizens report local issues, universities propose solutions, and industry & government turn them into real-world impact."
        primaryCta={primary}
        secondaryCta={secondary}
        stats={[
          { label: 'Problems Reported', value: '1,240+' },
          { label: 'HEI Partners', value: '86' },
          { label: 'Industry Partners', value: '54' },
          { label: 'Implemented', value: '312' },
        ]}
      />

      {/* How it works */}
      <section className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-extrabold text-primary-navy sm:text-4xl">How it works</h2>
          <p className="mt-3 text-ink-soft">Four steps from a local complaint to measurable change.</p>
        </div>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((s) => (
            <Card key={s.n} className="relative">
              <div className="text-4xl font-extrabold text-primary/15">{s.n}</div>
              <h3 className="mt-3 text-lg font-bold text-primary-navy">{s.title}</h3>
              <p className="mt-2 text-sm text-ink-soft">{s.body}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="bg-bg-soft py-20">
        <div className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-extrabold text-primary-navy sm:text-4xl">Built for every actor</h2>
          </div>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((f) => (
              <Card key={f.title} hover>
                <Badge color="primary">{f.title}</Badge>
                <p className="mt-3 text-sm text-ink-soft">{f.body}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-20 text-center">
        <h2 className="text-3xl font-extrabold text-primary-navy sm:text-4xl">Report a problem today</h2>
        <p className="mt-3 text-ink-soft max-w-2xl mx-auto">
          Your community knows what needs fixing. Help us route it to the people who can solve it.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          {user ? (
            <>
              <Link to={homeForRole(user.role)}>
                <Button size="lg">Go to Dashboard</Button>
              </Link>
              <Link to="/problems">
                <Button size="lg" variant="secondary">Browse Problems</Button>
              </Link>
              <Link to={mapLink.to}>
                <Button size="lg" variant="secondary">{mapLink.label}</Button>
              </Link>
            </>
          ) : (
            <>
              <Link to="/register">
                <Button size="lg">Create Account</Button>
              </Link>
              <Link to="/problems">
                <Button size="lg" variant="secondary">Browse Problems</Button>
              </Link>
              <Link to={mapLink.to}>
                <Button size="lg" variant="secondary">{mapLink.label}</Button>
              </Link>
            </>
          )}
        </div>
      </section>

      <footer className="border-t border-line py-8">
        <div className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 text-sm text-ink-muted">
          © {new Date().getFullYear()} Socio Connect — Societal Innovation Collaboration Portal.
        </div>
      </footer>
    </div>
  );
}
