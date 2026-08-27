// Status -> design.txt §7 color mapping
const statusStyles = {
  pending_validation: 'bg-tag-warning text-white',
  validated: 'bg-tag-blue text-white',
  open: 'bg-tag-blue text-white',
  rejected: 'bg-tag-danger text-white',
  duplicate: 'bg-tag-danger text-white',
  in_review: 'bg-tag-navy text-white',
  proposal_submitted: 'bg-tag-navy text-white',
  in_collaboration: 'bg-accent-cyan text-primary-navy',
  prototype: 'bg-accent-cyan text-primary-navy',
  pilot: 'bg-tag-success text-white',
  implementation: 'bg-tag-success text-white',
  implemented: 'bg-bg-soft text-ink-soft',
  closed: 'bg-bg-soft text-ink-soft',
};

const priorityStyles = {
  low: 'bg-bg-soft text-ink-soft',
  medium: 'bg-tag-warning text-white',
  high: 'bg-tag-blue text-white',
  critical: 'bg-tag-danger text-white',
};

const roleLabels = {
  citizen: 'Citizen',
  student: 'Student',
  faculty: 'Faculty Mentor',
  university_admin: 'University',
  industry: 'Industry',
  government: 'Government',
  admin: 'Admin',
};

const roleStyles = {
  citizen: 'bg-tag-blue text-white',
  student: 'bg-accent-cyan text-primary-navy',
  faculty: 'bg-tag-navy text-white',
  university_admin: 'bg-primary-navy text-white',
  industry: 'bg-tag-success text-white',
  government: 'bg-tag-warning text-white',
  admin: 'bg-tag-danger text-white',
};

export function Badge({ children, variant = 'solid', color = 'primary', size = 'md', className = '' }) {
  const sizes = { sm: 'text-[11px] px-2 py-0.5', md: 'text-xs px-2.5 py-1' };
  if (variant === 'outline') {
    return (
      <span className={`inline-flex items-center rounded-full border border-line-soft text-ink-soft font-semibold ${sizes[size]} ${className}`}>
        {children}
      </span>
    );
  }
  const palette = {
    primary: 'bg-tag-blue text-white',
    navy: 'bg-tag-navy text-white',
    success: 'bg-tag-success text-white',
    warning: 'bg-tag-warning text-white',
    danger: 'bg-tag-danger text-white',
    cyan: 'bg-accent-cyan text-primary-navy',
    muted: 'bg-bg-soft text-ink-soft',
  };
  return (
    <span className={`inline-flex items-center rounded-full font-semibold uppercase tracking-wide ${palette[color]} ${sizes[size]} ${className}`}>
      {children}
    </span>
  );
}

export function StatusBadge({ status, size = 'md' }) {
  const cls = statusStyles[status] || 'bg-bg-soft text-ink-soft';
  const sizes = { sm: 'text-[11px] px-2 py-0.5', md: 'text-xs px-2.5 py-1' };
  return (
    <span className={`inline-flex items-center rounded-full font-semibold capitalize ${cls} ${sizes[size]}`}>
      {status?.replace(/_/g, ' ')}
    </span>
  );
}

export function PriorityBadge({ priority, size = 'md' }) {
  const cls = priorityStyles[priority] || 'bg-bg-soft text-ink-soft';
  const sizes = { sm: 'text-[11px] px-2 py-0.5', md: 'text-xs px-2.5 py-1' };
  return (
    <span className={`inline-flex items-center rounded-full font-semibold capitalize ${cls} ${sizes[size]}`}>
      {priority}
    </span>
  );
}

export function RoleBadge({ role, size = 'md' }) {
  const cls = roleStyles[role] || 'bg-bg-soft text-ink-soft';
  const sizes = { sm: 'text-[11px] px-2 py-0.5', md: 'text-xs px-2.5 py-1' };
  return (
    <span className={`inline-flex items-center rounded-full font-semibold ${cls} ${sizes[size]}`}>
      {roleLabels[role] || role}
    </span>
  );
}

export default Badge;
