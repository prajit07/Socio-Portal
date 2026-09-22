import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { problemsApi } from '../api/client';
import { Button, Modal, TextArea, Alert } from './ui';

export default function ProblemDeleteButton({ problemId, canDelete, onDeleted }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  if (!canDelete) return null;

  const handleDelete = async () => {
    if (reason.trim().length < 1) {
      setError(t('Please provide a reason for deleting this problem.'));
      return;
    }
    setBusy(true);
    setError('');
    try {
      await problemsApi.remove(problemId, reason.trim());
      setOpen(false);
      if (onDeleted) onDeleted();
    } catch (e) {
      setError(e.response?.data?.detail || t('Failed to delete the problem.'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Button variant="danger" size="sm" onClick={() => { setError(''); setReason(''); setOpen(true); }}>
        {t('Delete')}
      </Button>

      <Modal open={open} onClose={() => setOpen(false)} title={t('Delete this problem?')} size="md">
        <p className="text-sm text-ink-soft mb-3">
          {t("This will remove the problem from listings. Please tell us why you're deleting it — the reason is recorded for review.")}
        </p>
        {error && <Alert variant="danger" className="mb-3">{error}</Alert>}
        <TextArea
          rows={3}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder={t('Reason for deletion (e.g. already resolved, incorrect details, duplicate…)')}
        />
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>{t('Cancel')}</Button>
          <Button variant="danger" onClick={handleDelete} loading={busy}>{t('Delete Problem')}</Button>
        </div>
      </Modal>
    </>
  );
}
