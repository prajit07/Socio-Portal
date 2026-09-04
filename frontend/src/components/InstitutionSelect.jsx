import { useState, useEffect, useRef, useMemo } from 'react';
import { universitiesApi } from '../api/client';
import { Input } from './ui';

export default function InstitutionSelect({ value, label, onChange, error }) {
  const [query, setQuery] = useState(label || '');
  const [all, setAll] = useState([]); // [{id, name}]
  const [loaded, setLoaded] = useState(false);
  const [open, setOpen] = useState(false);
  const boxRef = useRef(null);

  useEffect(() => {
    function onDocClick(e) {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  // Load the full id+name directory ONCE (then filter locally => instant search).
  // Cache in sessionStorage so navigating between register steps is instant.
  useEffect(() => {
    let active = true;
    const cached = sessionStorage.getItem('socio_inst_options');
    if (cached) {
      try {
        // eslint-disable-next-line react/set-state-in-effect -- hydrates local cache from sessionStorage on mount
        setAll(JSON.parse(cached));
        // eslint-disable-next-line react/set-state-in-effect -- hydrates local cache from sessionStorage on mount
        setLoaded(true);
        return;
      } catch { /* fall through */ }
    }
    universitiesApi.options().then((r) => {
      if (!active) return;
      const data = r.data || [];
      setAll(data);
      setLoaded(true);
      try { sessionStorage.setItem('socio_inst_options', JSON.stringify(data)); } catch { /* ignore */ }
    }).catch(() => active && setLoaded(true));
    return () => { active = false; };
  }, []);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (q.length < 2) return [];
    return all.filter((x) => x.name.toLowerCase().includes(q)).slice(0, 25);
  }, [query, all]);

  const exactExists = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q.length >= 2 && all.some((x) => x.name.toLowerCase() === q);
  }, [query, all]);

  const select = (inst) => {
    onChange(inst.id, inst.name);
    setQuery(inst.name);
    setOpen(false);
  };

  const addMissing = async () => {
    try {
      const res = await universitiesApi.suggest({ name: query.trim() });
      const inst = res.data;
      setAll((prev) => [...prev, { id: inst.id, name: inst.name }]);
      select(inst);
    } catch {
      // ignore
    }
  };

  return (
    <div className="relative" ref={boxRef}>
      <label className="block text-sm font-semibold text-ink mb-2">Your Institution</label>
      <Input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
          if (!e.target.value) onChange('', '');
        }}
        onFocus={() => setOpen(true)}
        placeholder="Search your college / university…"
        required
        error={error}
      />
      {open && query.trim().length >= 2 && (
        <div className="absolute z-20 mt-1 w-full max-h-64 overflow-auto rounded-btn border border-line bg-white shadow-lg">
          {!loaded && <div className="px-3 py-2 text-sm text-ink-muted">Loading directory…</div>}
          {loaded && results.length === 0 && (
            <button
              type="button"
              onClick={addMissing}
              className="block w-full text-left px-3 py-2 text-sm hover:bg-bg-soft border-b border-line"
            >
              Can't find it? <span className="font-semibold text-primary">Add &ldquo;{query.trim()}&rdquo;</span>
            </button>
          )}
          {results.map((inst) => (
            <button
              type="button"
              key={inst.id}
              onClick={() => select(inst)}
              className="block w-full text-left px-3 py-2 text-sm hover:bg-bg-soft border-b border-line last:border-0"
            >
              <span className="font-semibold text-primary-navy">{inst.name}</span>
            </button>
          ))}
          {loaded && results.length > 0 && !exactExists && (
            <button
              type="button"
              onClick={addMissing}
              className="block w-full text-left px-3 py-2 text-sm hover:bg-bg-soft text-ink-muted"
            >
              Not listed? <span className="font-semibold text-primary">Add &ldquo;{query.trim()}&rdquo;</span>
            </button>
          )}
        </div>
      )}
      {value && <p className="mt-1 text-xs text-ink-muted">Selected: <span className="font-semibold">{label}</span></p>}
    </div>
  );
}
