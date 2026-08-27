import { useState } from 'react';

const styles = {
  info: 'bg-bg-soft border-line-soft text-primary-navy',
  success: 'bg-tag-success/10 border-tag-success/30 text-tag-success',
  warning: 'bg-tag-warning/10 border-tag-warning/30 text-tag-warning',
  danger: 'bg-tag-danger/10 border-tag-danger/30 text-tag-danger',
};

export function Alert({ children, variant = 'info', dismissible = false, onDismiss, className = '' }) {
  const [visible, setVisible] = useState(true);
  if (!visible) return null;
  return (
    <div className={`flex items-start gap-3 rounded-card border p-4 ${styles[variant]} ${className}`}>
      <div className="flex-1 text-sm font-medium">{children}</div>
      {dismissible && (
        <button
          onClick={() => (onDismiss ? onDismiss() : setVisible(false))}
          className="flex-shrink-0 p-1 rounded hover:bg-black/10 transition-colors"
          aria-label="Dismiss"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
}

export function Toast({ toasts = [], onClose }) {
  return (
    <div className="fixed top-4 right-4 z-[100] space-y-2 w-80 max-w-[90vw]">
      {toasts.map((t) => (
        <Alert key={t.id} variant={t.variant || 'info'} dismissible onDismiss={() => onClose?.(t.id)}>
          {t.message}
        </Alert>
      ))}
    </div>
  );
}

export default Alert;
