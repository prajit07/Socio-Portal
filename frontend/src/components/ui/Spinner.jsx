export function Spinner({ className = 'w-6 h-6' }) {
  return (
    <svg className={`${className} animate-spin text-primary`} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
  );
}

export function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-soft">
      <Spinner className="w-10 h-10" />
    </div>
  );
}

export function CardSkeleton({ className = '' }) {
  return (
    <div className={`bg-white border border-line rounded-card p-6 ${className}`}>
      <div className="h-4 w-1/3 bg-bg-soft rounded mb-4 animate-pulse" />
      <div className="h-3 w-full bg-bg-soft rounded mb-2 animate-pulse" />
      <div className="h-3 w-2/3 bg-bg-soft rounded animate-pulse" />
    </div>
  );
}

export function ListSkeleton({ count = 4 }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

export default Spinner;
