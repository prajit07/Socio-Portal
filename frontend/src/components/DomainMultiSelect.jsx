import { DOMAIN_OPTIONS } from '../constants/domains';

export default function DomainMultiSelect({ selected = [], onChange }) {
  const list = DOMAIN_OPTIONS;
  const toggle = (opt) => {
    if (selected.includes(opt)) onChange(selected.filter((o) => o !== opt));
    else onChange([...selected, opt]);
  };
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
      {list.map((opt) => {
        const active = selected.includes(opt);
        return (
          <button
            type="button"
            key={opt}
            onClick={() => toggle(opt)}
            className={`flex items-center gap-2 rounded-btn border px-3 py-2 text-sm text-left transition ${
              active ? 'border-primary bg-bg-soft text-primary-navy' : 'border-line text-ink-soft hover:border-primary'
            }`}
          >
            <span
              className={`flex h-4 w-4 flex-none items-center justify-center rounded border text-[10px] ${
                active ? 'border-primary bg-primary text-white' : 'border-line text-transparent'
              }`}
            >
              ✓
            </span>
            <span className="truncate">{opt}</span>
          </button>
        );
      })}
    </div>
  );
}
