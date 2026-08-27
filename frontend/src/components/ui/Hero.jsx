import { Link } from 'react-router-dom';

export default function Hero({
  eyebrow,
  title,
  highlight,
  subtitle,
  primaryCta,
  secondaryCta,
  stats,
}) {
  return (
    <section className="relative overflow-hidden bg-bg-soft">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            'radial-gradient(60% 60% at 50% 0%, rgba(34,199,242,0.12) 0%, rgba(245,248,255,0) 70%)',
        }}
      />
      <div className="relative mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 pt-20 pb-16 text-center">
        {eyebrow && (
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-line bg-white px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-ink-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-tag-success" />
            {eyebrow}
          </div>
        )}
        <h1 className="mx-auto max-w-[900px] text-4xl font-extrabold leading-[1.05] tracking-tight text-primary-navy sm:text-5xl lg:text-6xl">
          {title}{' '}
          {highlight && (
            <span className="bg-gradient-to-r from-primary to-accent-cyan bg-clip-text text-transparent">
              {highlight}
            </span>
          )}
        </h1>
        {subtitle && (
          <p className="mx-auto mt-6 max-w-[640px] text-lg text-ink-soft">{subtitle}</p>
        )}
        {(primaryCta || secondaryCta) && (
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            {primaryCta && (
              <Link to={primaryCta.to}>
                <button className="rounded-btn bg-primary px-6 py-3 text-base font-bold text-white hover:bg-primary-dark">
                  {primaryCta.label}
                </button>
              </Link>
            )}
            {secondaryCta && (
              <Link to={secondaryCta.to}>
                <button className="rounded-btn border border-primary-navy px-6 py-3 text-base font-bold text-primary-navy hover:bg-bg-soft">
                  {secondaryCta.label}
                </button>
              </Link>
            )}
          </div>
        )}
        {stats && (
          <div className="mx-auto mt-14 grid max-w-3xl grid-cols-2 gap-6 sm:grid-cols-4">
            {stats.map((s) => (
              <div key={s.label} className="text-center">
                <div className="text-3xl font-extrabold text-primary-navy">{s.value}</div>
                <div className="mt-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
                  {s.label}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
