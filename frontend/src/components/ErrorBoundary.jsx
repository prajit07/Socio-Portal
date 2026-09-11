import { Component } from 'react';

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
      return (
        <div className="min-h-screen flex items-center justify-center bg-bg-soft px-4">
          <div className="max-w-md w-full text-center">
            <div className="text-5xl mb-4">&#9888;</div>
            <h2 className="text-xl font-bold text-primary-navy mb-2">Something went wrong</h2>
            <p className="text-ink-soft text-sm mb-6">
              An unexpected error occurred while loading this page.
            </p>
            <button
              onClick={this.handleRetry}
              className="rounded-btn bg-primary px-6 py-2.5 text-sm font-bold text-white hover:bg-primary-dark transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
