import { Component } from 'react';
import { useTranslation } from 'react-i18next';

function ErrorFallback({ onRetry }) {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-soft px-4">
      <div className="max-w-md w-full text-center">
        <div className="text-5xl mb-4">&#9888;</div>
        <h2 className="text-xl font-bold text-primary-navy mb-2">{t('Something went wrong')}</h2>
        <p className="text-ink-soft text-sm mb-6">
          {t('An unexpected error occurred while loading this page.')}
        </p>
        <button
          onClick={onRetry}
          className="rounded-btn bg-primary px-6 py-2.5 text-sm font-bold text-white hover:bg-primary-dark transition-colors"
        >
          {t('Try Again')}
        </button>
      </div>
    </div>
  );
}

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return <ErrorFallback onRetry={this.handleRetry} />;
    }
    return this.props.children;
  }
}
