import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const roleLabels = {
  citizen: 'Citizen',
  student: 'Student',
  faculty: 'Faculty Mentor',
  university_admin: 'University',
  industry: 'Industry',
  government: 'Government',
  admin: 'Admin',
};

const navItems = {
  citizen: [
    { path: '/citizen/dashboard', label: 'My Problems' },
    { path: '/citizen/submit-problem', label: 'Report Problem' },
  ],
  student: [
    { path: '/university/dashboard', label: 'Workspace' },
    { path: '/problems', label: 'Problems' },
  ],
  faculty: [
    { path: '/university/dashboard', label: 'Workspace' },
    { path: '/problems', label: 'Problems' },
  ],
  university_admin: [
    { path: '/university/dashboard', label: 'Workspace' },
    { path: '/university/teams/new', label: 'Form Team' },
    { path: '/problems', label: 'Problems' },
  ],
  industry: [
    { path: '/industry/dashboard', label: 'Portal' },
    { path: '/problems', label: 'Matched' },
  ],
  government: [{ path: '/gov/dashboard', label: 'Dashboard' }],
  admin: [{ path: '/admin', label: 'Admin' }],
};

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2">
      <span className="flex h-9 w-9 items-center justify-center rounded-btn bg-primary text-white">
        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z" />
        </svg>
      </span>
      <span className="text-lg font-extrabold text-primary-navy tracking-tight">Socio Connect</span>
    </Link>
  );
}

export default function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const items = user ? navItems[user.role] || [] : [];

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) =>
    location.pathname === path || (path !== '/' && location.pathname.startsWith(path));

  return (
    <nav className="sticky top-0 z-50 h-[72px] bg-white border-b border-line shadow-nav">
      <div className="mx-auto flex h-full max-w-[1280px] items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Logo />
          {user && (
            <div className="hidden md:flex items-center gap-1">
              {items.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`relative px-3 py-2 text-sm font-semibold transition-colors ${
                    isActive(item.path) ? 'text-primary' : 'text-ink-soft hover:text-primary-navy'
                  }`}
                >
                  {item.label}
                  {isActive(item.path) && (
                    <span className="absolute -bottom-[1px] left-3 right-3 h-0.5 rounded bg-primary" />
                  )}
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="hidden md:flex items-center gap-3">
          {!user ? (
            <>
              <Link to="/login">
                <button className="rounded-btn border border-line-soft px-4 py-2 text-sm font-bold text-ink hover:bg-bg-soft">
                  Log in
                </button>
              </Link>
              <Link to="/register">
                <button className="rounded-btn bg-primary px-4 py-2 text-sm font-bold text-white hover:bg-primary-dark">
                  Get Started
                </button>
              </Link>
            </>
          ) : (
            <>
              <Link to="/settings" className="text-sm font-semibold text-ink hover:text-primary">Settings</Link>
              <span className="text-sm text-ink-soft">
                {user.name} · <span className="font-semibold text-primary-navy">{roleLabels[user.role] || user.role}</span>
              </span>
              <button
                onClick={handleLogout}
                className="rounded-btn border border-line-soft px-4 py-2 text-sm font-bold text-ink hover:bg-bg-soft"
              >
                Log out
              </button>
            </>
          )}
        </div>

        <button className="md:hidden p-2 text-ink" onClick={() => setOpen((v) => !v)} aria-label="Menu">
          <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-line bg-white px-4 py-3 space-y-1">
          {items.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setOpen(false)}
              className={`block rounded-btn px-3 py-2 text-sm font-semibold ${isActive(item.path) ? 'bg-bg-soft text-primary' : 'text-ink-soft'}`}
            >
              {item.label}
            </Link>
          ))}
          {!user ? (
            <div className="flex gap-2 pt-2">
              <Link to="/login" onClick={() => setOpen(false)} className="flex-1">
                <button className="w-full rounded-btn border border-line-soft px-4 py-2 text-sm font-bold">Log in</button>
              </Link>
              <Link to="/register" onClick={() => setOpen(false)} className="flex-1">
                <button className="w-full rounded-btn bg-primary px-4 py-2 text-sm font-bold text-white">Get Started</button>
              </Link>
            </div>
          ) : (
            <>
              <Link
                to="/settings"
                onClick={() => setOpen(false)}
                className="block rounded-btn px-3 py-2 text-sm font-semibold text-ink-soft hover:bg-bg-soft"
              >
                Settings
              </Link>
              <button onClick={handleLogout} className="w-full rounded-btn border border-line-soft px-4 py-2 text-sm font-bold">
                Log out
              </button>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
