import { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

export function Modal({ open, onClose, title, children, footer, size = 'md' }) {
  const ref = useRef(null);
  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose?.();
    }
    if (open) document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;
  const sizes = { sm: 'max-w-md', md: 'max-w-lg', lg: 'max-w-2xl' };
  return createPortal(
    <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-primary-deep/50 backdrop-blur-sm" onClick={onClose} />
      <div
        ref={ref}
        className={`relative bg-white rounded-card shadow-card w-full ${sizes[size]} max-h-[90vh] flex flex-col`}
      >
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-line">
            <h3 className="text-lg font-bold text-primary-navy">{title}</h3>
            <button onClick={onClose} className="p-1 rounded hover:bg-bg-soft" aria-label="Close">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
        <div className="px-6 py-4 overflow-y-auto">{children}</div>
        {footer && <div className="px-6 py-4 border-t border-line flex justify-end gap-3">{footer}</div>}
      </div>
    </div>,
    document.body
  );
}

export function ConfirmDialog({ open, title, message, confirmLabel = 'Confirm', onConfirm, onCancel, danger = false }) {
  return (
    <Modal
      open={open}
      onClose={onCancel}
      title={title}
      size="sm"
      footer={
        <>
          <button onClick={onCancel} className="px-4 py-2.5 text-sm font-bold rounded-btn border border-line-soft hover:bg-bg-soft">
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2.5 text-sm font-bold rounded-btn text-white ${danger ? 'bg-tag-danger hover:brightness-95' : 'bg-primary hover:bg-primary-dark'}`}
          >
            {confirmLabel}
          </button>
        </>
      }
    >
      <p className="text-sm text-ink-soft">{message}</p>
    </Modal>
  );
}

export default Modal;
