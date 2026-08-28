import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from 'react-i18next';

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
  government: [
    { path: '/gov/dashboard', label: 'Dashboard' },
    { path: '/gov/analytics', label: 'Analytics' },
    { path: '/gov/impact-reports', label: 'Impact Reports' },
    { path: '/problems', label: 'Problems' },
    { path: '/map', label: 'Map' },
  ],
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
  const { t, i18n } = useTranslation();

  const items = user ? navItems[user.role] || [] : [];

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'hi', name: 'हिंदी' },
    { code: 'ta', name: 'தமிழ்' },
    { code: 'te', name: 'తెలుగు' },
    { code: 'ml', name: 'മലയാളം' },
    { code: 'kn', name: 'ಕನ್ನಡ' },
    { code: 'mr', name: 'मराठी' },
    { code: 'bn', name: 'বাংলা' },
    { code: 'gu', name: 'ગુજરાતી' },
    { code: 'pa', name: 'ਪੰਜਾਬੀ' },
  ];

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
                  {t(item.label)}
                  {isActive(item.path) && (
                    <span className="absolute -bottom-[1px] left-3 right-3 h-0.5 rounded bg-primary" />
                  )}
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="hidden md:flex items-center gap-3">
          <select 
            value={i18n.resolvedLanguage} 
            onChange={(e) => i18n.changeLanguage(e.target.value)}
            className="text-xs font-semibold bg-bg-soft border border-line rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
          >
            {languages.map((l) => (
              <option key={l.code} value={l.code}>{l.name}</option>
            ))}
          </select>
          
          <Link to="/problems/map" className="text-sm font-semibold text-ink-soft hover:text-primary">
            {t('Public Map')}
          </Link>
          {!user ? (
            <>
              <Link to="/login">
                <button className="rounded-btn border border-line-soft px-4 py-2 text-sm font-bold text-ink hover:bg-bg-soft">
                  {t('Log in')}
                </button>
              </Link>
              <Link to="/register">
                <button className="rounded-btn bg-primary px-4 py-2 text-sm font-bold text-white hover:bg-primary-dark">
                  {t('Get Started')}
                </button>
              </Link>
            </>
          ) : (
            <>
              <Link
                to="/settings"
                className="p-2 rounded-btn text-ink-soft hover:text-primary hover:bg-bg-soft"
                aria-label="Settings"
                title={t('Settings')}
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.265.217-.384.526-.322.838a6.82 6.82 0 010 .582c-.062.312.057.62.322.838l1.003.827c.407.336.54.872.26 1.43l-1.296 2.247a1.125 1.125 0 01-1.37.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.2 6.2 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.063-.374-.313-.686-.645-.87a6.2 6.2 0 01-.22-.127c-.324-.196-.72-.257-1.075-.124l-1.217.456a1.125 1.125 0 01-1.37-.49l-1.296-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.265-.217.384-.526.322-.838a6.82 6.82 0 010-.582c.062-.312-.057-.62-.322-.838l-1.003-.827a1.125 1.125 0 01-.26-1.43l1.296-2.247a1.125 1.125 0 011.37-.491l1.217.456c.355.133.75.072 1.076-.124.072-.044.146-.087.22-.128.331-.183.581-.495.644-.869l.213-1.281z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </Link>
              <span className="hidden lg:inline text-sm text-ink-soft">
                {user.name} · <span className="font-semibold text-primary-navy">{t(roleLabels[user.role] || user.role)}</span>
              </span>
              <button
                onClick={handleLogout}
                className="rounded-btn border border-line-soft px-4 py-2 text-sm font-bold text-ink hover:bg-bg-soft"
              >
                {t('Log out')}
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
          <div className="pb-2">
            <select 
              value={i18n.resolvedLanguage} 
              onChange={(e) => i18n.changeLanguage(e.target.value)}
              className="w-full text-sm font-semibold bg-bg-soft border border-line rounded px-3 py-2 focus:outline-none"
            >
              {languages.map((l) => (
                <option key={l.code} value={l.code}>{l.name}</option>
              ))}
            </select>
          </div>
          {items.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setOpen(false)}
              className={`block rounded-btn px-3 py-2 text-sm font-semibold ${isActive(item.path) ? 'bg-bg-soft text-primary' : 'text-ink-soft'}`}
            >
              {t(item.label)}
            </Link>
          ))}
          {!user ? (
            <div className="flex gap-2 pt-2">
              <Link to="/login" onClick={() => setOpen(false)} className="flex-1">
                <button className="w-full rounded-btn border border-line-soft px-4 py-2 text-sm font-bold">{t('Log in')}</button>
              </Link>
              <Link to="/register" onClick={() => setOpen(false)} className="flex-1">
                <button className="w-full rounded-btn bg-primary px-4 py-2 text-sm font-bold text-white">{t('Get Started')}</button>
              </Link>
            </div>
           ) : (
            <>
              <Link
                to="/settings"
                onClick={() => setOpen(false)}
                className="flex items-center gap-2 rounded-btn px-3 py-2 text-sm font-semibold text-ink-soft hover:bg-bg-soft"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.265.217-.384.526-.322.838a6.82 6.82 0 010 .582c-.062.312.057.62.322.838l1.003.827c.407.336.54.872.26 1.43l-1.296 2.247a1.125 1.125 0 01-1.37.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.2 6.2 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.063-.374-.313-.686-.645-.87a6.2 6.2 0 01-.22-.127c-.324-.196-.72-.257-1.075-.124l-1.217.456a1.125 1.125 0 01-1.37-.49l-1.296-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.265-.217.384-.526.322-.838a6.82 6.82 0 010-.582c.062-.312-.057-.62-.322-.838l-1.003-.827a1.125 1.125 0 01-.26-1.43l1.296-2.247a1.125 1.125 0 011.37-.491l1.217.456c.355.133.75.072 1.076-.124.072-.044.146-.087.22-.128.331-.183.581-.495.644-.869l.213-1.281z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {t('Settings')}
              </Link>
              <button onClick={handleLogout} className="w-full rounded-btn border border-line-soft px-4 py-2 text-sm font-bold">
                {t('Log out')}
              </button>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
