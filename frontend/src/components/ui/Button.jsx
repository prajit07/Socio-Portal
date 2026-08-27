import { forwardRef } from 'react';

const variants = {
  primary:
    'bg-primary text-white hover:bg-primary-dark shadow-sm',
  secondary:
    'bg-transparent text-primary-navy border border-primary-navy hover:bg-bg-soft',
  ghost:
    'bg-transparent text-ink border border-line-soft hover:bg-bg-soft',
  success:
    'bg-tag-success text-white hover:brightness-95 shadow-sm',
  danger:
    'bg-tag-danger text-white hover:brightness-95 shadow-sm',
  link: 'bg-transparent text-primary hover:text-primary-dark underline-offset-4 hover:underline',
};

const sizes = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2.5 text-sm',
  lg: 'px-6 py-3 text-base',
};

const Button = forwardRef(function Button(
  { children, variant = 'primary', size = 'md', className = '', loading = false, disabled, type = 'button', ...props },
  ref
) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 font-bold tracking-wide rounded-btn transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {loading && (
        <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
      )}
      {children}
    </button>
  );
});

export default Button;
