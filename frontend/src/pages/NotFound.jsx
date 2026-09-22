import { Link } from 'react-router-dom';
import { Button } from '../components/ui';
import { useTranslation } from 'react-i18next';

export default function NotFound() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-bg-soft text-center px-4">
      <div className="text-6xl font-extrabold text-primary">404</div>
      <h1 className="mt-4 text-2xl font-bold text-primary-navy">{t('Page not found')}</h1>
      <p className="mt-2 text-ink-soft">{t('The page you are looking for does not exist.')}</p>
      <Link to="/" className="mt-6">
        <Button>{t('Back to Home')}</Button>
      </Link>
    </div>
  );
}
