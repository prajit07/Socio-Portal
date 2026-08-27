import { forwardRef } from 'react';

export const Input = forwardRef(function Input(
  { label, hint, error, className = '', id, ...props },
  ref
) {
  const inputId = id || props.name;
  return (
    <div className={className}>
      {label && (
        <label htmlFor={inputId} className="block text-sm font-semibold text-ink mb-1.5">
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={inputId}
        className={`w-full px-4 py-2.5 rounded-btn border border-line bg-white text-ink placeholder:text-ink-muted focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-colors ${
          error ? 'border-tag-danger' : ''
        }`}
        {...props}
      />
      {hint && !error && <p className="mt-1 text-xs text-ink-muted">{hint}</p>}
      {error && <p className="mt-1 text-xs text-tag-danger">{error}</p>}
    </div>
  );
});

export const TextArea = forwardRef(function TextArea(
  { label, hint, error, rows = 4, className = '', id, ...props },
  ref
) {
  const inputId = id || props.name;
  return (
    <div className={className}>
      {label && (
        <label htmlFor={inputId} className="block text-sm font-semibold text-ink mb-1.5">
          {label}
        </label>
      )}
      <textarea
        ref={ref}
        id={inputId}
        rows={rows}
        className={`w-full px-4 py-2.5 rounded-btn border border-line bg-white text-ink placeholder:text-ink-muted focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-colors resize-y ${
          error ? 'border-tag-danger' : ''
        }`}
        {...props}
      />
      {hint && !error && <p className="mt-1 text-xs text-ink-muted">{hint}</p>}
      {error && <p className="mt-1 text-xs text-tag-danger">{error}</p>}
    </div>
  );
});

export default Input;
