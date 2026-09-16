import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Hero from '../components/ui/Hero';
import { Card, Button, Badge, StatusBadge } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from 'react-i18next';
import { homeForRole } from '../lib/routes';
import { problemsApi } from '../api/client';

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
  const { t } = useTranslation();
  const [publicProblems, setPublicProblems] = useState([]);
  const [publicLoading, setPublicLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        // Public endpoint — works for guests, no login required.
        const res = await problemsApi.list({ limit: 12 });
        if (!cancelled) setPublicProblems(Array.isArray(res.data) ? res.data : []);
      } catch {
        if (!cancelled) setPublicProblems([]);
      } finally {
        if (!cancelled) setPublicLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const primary = user
    ? { to: homeForRole(user.role), label: t('Go to Dashboard') }
    : { to: '/register', label: t('Get Started') };
  const secondary = user ? { to: '/problems', label: t('Browse Problems') } : { to: '/login', label: t('Sign In') };
  const mapLink = { to: '/problems/map', label: t('View Public Map') };

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <Hero
        eyebrow={t("Societal Innovation Collaboration Portal")}
        title={t("Turn community problems into")}
        highlight={t("collective solutions")}
        subtitle={t("A civic-tech platform where citizens report local issues, universities propose solutions, and industry & government turn them into real-world impact.")}
        primaryCta={primary}
        secondaryCta={secondary}
        stats={[
          { label: t('Problems Reported'), value: '1,240+' },
          { label: t('HEI Partners'), value: '86' },
          { label: t('Industry Partners'), value: '54' },
          { label: t('Implemented'), value: '312' },
        ]}
      />

      {/* How it works */}
      <section className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-extrabold text-primary-navy sm:text-4xl">{t('How it works')}</h2>
          <p className="mt-3 text-ink-soft">{t('Four steps from a local complaint to measurable change.')}</p>
        </div>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((s) => (
            <Card key={s.n} className="relative">
              <div className="text-4xl font-extrabold text-primary/15">{s.n}</div>
              <h3 className="mt-3 text-lg font-bold text-primary-navy">{t(s.title)}</h3>
              <p className="mt-2 text-sm text-ink-soft">{t(s.body)}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="bg-bg-soft py-20">
        <div className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-extrabold text-primary-navy sm:text-4xl">{t('Built for every actor')}</h2>
          </div>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((f) => (
              <Card key={f.title} hover>
                <Badge color="primary">{t(f.title)}</Badge>
                <p className="mt-3 text-sm text-ink-soft">{t(f.body)}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Live public problems — visible to guests, no login required */}
      <section className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-20">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-8">
          <div>
            <h2 className="text-3xl font-extrabold text-primary-navy sm:text-4xl">{t('Live public problem map')}</h2>
            <p className="mt-3 text-ink-soft max-w-2xl">
              {t('Every report from every citizen — open for guests to explore. No account needed to see what needs fixing.')}
            </p>
          </div>
          <div className="flex gap-3">
            <Link to="/problems/map">
              <Button size="lg">{t('Open full map')}</Button>
            </Link>
            <Link to="/problems">
              <Button size="lg" variant="secondary">{t('Browse Problems')}</Button>
            </Link>
          </div>
        </div>
        {publicLoading ? (
          <p className="text-ink-muted text-sm">{t('Loading public problems…')}</p>
        ) : publicProblems.length === 0 ? (
          <Card className="text-center py-10 text-ink-soft">
            {t('No public problems yet — be the first to report one.')}
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {publicProblems.slice(0, 6).map((p) => (
              <Link key={p.id} to={`/problems/${p.id}`}>
                <Card hover>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-bold text-primary-navy line-clamp-2">{p.title}</h3>
                    <StatusBadge status={p.status} size="sm" />
                  </div>
                  <p className="text-sm text-ink-soft mt-2 line-clamp-3">{p.description}</p>
                  <div className="mt-3 text-xs text-ink-muted">
                    {[p.address, p.ai_category].filter(Boolean).join(' · ') || new Date(p.created_at).toLocaleDateString()}
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-20 text-center">
        <h2 className="text-3xl font-extrabold text-primary-navy sm:text-4xl">{t('Report a problem today')}</h2>
        <p className="mt-3 text-ink-soft max-w-2xl mx-auto">
          {t('Your community knows what needs fixing. Help us route it to the people who can solve it.')}
        </p>
        <div className="mt-8 flex justify-center gap-4">
          {user ? (
            <>
              <Link to={homeForRole(user.role)}>
                <Button size="lg">{t('Go to Dashboard')}</Button>
              </Link>
              <Link to="/problems">
                <Button size="lg" variant="secondary">{t('Browse Problems')}</Button>
              </Link>
              <Link to={mapLink.to}>
                <Button size="lg" variant="secondary">{mapLink.label}</Button>
              </Link>
            </>
          ) : (
            <>
              <Link to="/register">
                <Button size="lg">{t('Create Account')}</Button>
              </Link>
              <Link to="/problems">
                <Button size="lg" variant="secondary">{t('Browse Problems')}</Button>
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
