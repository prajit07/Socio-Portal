export function StatCard({ label, value, sub, icon, accent = 'primary', className = '' }) {
  const accents = {
    primary: 'text-primary',
    success: 'text-tag-success',
    warning: 'text-tag-warning',
    danger: 'text-tag-danger',
    cyan: 'text-accent-cyan',
    navy: 'text-primary-navy',
  };
  return (
    <div className={`bg-white border border-line rounded-card p-6 ${className}`}>
      {icon && <div className={`mb-3 ${accents[accent]}`}>{icon}</div>}
      <div className="text-3xl font-extrabold text-primary-navy leading-none">{value}</div>
      <div className="mt-2 text-sm font-semibold text-ink">{label}</div>
      {sub && <div className="mt-1 text-xs text-ink-muted">{sub}</div>}
    </div>
  );
}

export default StatCard;
