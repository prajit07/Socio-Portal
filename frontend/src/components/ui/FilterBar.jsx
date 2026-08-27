export function FilterBar({ label, options = [], value, onChange, className = '' }) {
  return (
    <div className={`flex flex-wrap items-center gap-2 ${className}`}>
      {label && <span className="text-sm font-semibold text-ink-muted mr-1">{label}</span>}
      {options.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            onClick={() => onChange?.(opt.value)}
            className={`px-3.5 py-1.5 rounded-full text-sm font-semibold border transition-colors ${
              active
                ? 'bg-primary-navy text-white border-primary-navy'
                : 'bg-white text-ink-soft border-line-soft hover:border-primary'
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

export default FilterBar;
