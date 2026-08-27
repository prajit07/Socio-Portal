export function Card({ children, className = '', hover = false, padding = 'lg' }) {
  const pad = { none: '', sm: 'p-4', md: 'p-6', lg: 'p-8' }[padding];
  return (
    <div
      className={`bg-white border border-line rounded-card ${hover ? 'transition-all duration-200 hover:shadow-card hover:-translate-y-0.5' : ''} ${pad} ${className}`}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '' }) {
  return <div className={`mb-4 ${className}`}>{children}</div>;
}

export function CardContent({ children, className = '' }) {
  return <div className={className}>{children}</div>;
}

export function CardFooter({ children, className = '' }) {
  return <div className={`mt-4 pt-4 border-t border-line ${className}`}>{children}</div>;
}

export default Card;
