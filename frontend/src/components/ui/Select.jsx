import { forwardRef } from 'react';

export const Select = forwardRef(function Select(
  { label, hint, error, options = [], className = '', id, ...props },
  ref
) {
  const selectId = id || props.name;
  return (
    <div className={className}>
      {label && (
        <label htmlFor={selectId} className="block text-sm font-semibold text-ink mb-1.5">
          {label}
        </label>
      )}
      <select
        ref={ref}
        id={selectId}
        className={`w-full px-4 py-2.5 rounded-btn border border-line bg-white text-ink focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-colors ${
          error ? 'border-tag-danger' : ''
        }`}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {hint && !error && <p className="mt-1 text-xs text-ink-muted">{hint}</p>}
      {error && <p className="mt-1 text-xs text-tag-danger">{error}</p>}
    </div>
  );
});

export default Select;
