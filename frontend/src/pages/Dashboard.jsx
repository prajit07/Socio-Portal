import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { problemsApi } from '../api/client';
import Navbar from '../components/Navbar';

const roleDashboards = {
  citizen: {
    title: 'My Problems',
    subtitle: 'Track and manage your submitted problems',
    primaryAction: { label: 'Report New Problem', path: '/problems/new' },
    stats: ['submitted', 'categorized', 'in_progress', 'implemented'],
  },
  student: {
    title: 'My Solutions',
    subtitle: 'Browse problems and submit solutions',
    primaryAction: { label: 'Browse All Problems', path: '/problems' },
    stats: ['draft', 'submitted', 'accepted', 'implemented'],
  },
  faculty: {
    title: 'Faculty Dashboard',
    subtitle: 'Mentor students and review solutions',
    primaryAction: { label: 'Browse All Problems', path: '/problems' },
    stats: ['draft', 'submitted', 'under_review', 'accepted'],
  },
  university_admin: {
    title: 'University Admin Dashboard',
    subtitle: 'Manage university participation and categorize problems',
    primaryAction: { label: 'View All Problems', path: '/problems' },
    stats: ['submitted', 'categorized', 'matched', 'in_progress'],
  },
  industry: {
    title: 'Industry Dashboard',
    subtitle: 'Partner on solutions and mentor teams',
    primaryAction: { label: 'Browse All Problems', path: '/problems' },
    stats: ['solution_proposed', 'prototype', 'pilot_test', 'implemented'],
  },
  government: {
    title: 'Government Dashboard',
    subtitle: 'Monitor impact and oversee implementation',
    primaryAction: { label: 'View All Problems', path: '/problems' },
    stats: ['submitted', 'categorized', 'implemented', 'closed'],
  },
  admin: {
    title: 'Admin Dashboard',
    subtitle: 'Full system oversight and management',
    primaryAction: { label: 'View All Problems', path: '/problems' },
    stats: ['submitted', 'categorized', 'in_progress', 'implemented'],
  },
};

export default function Dashboard() {
  const { user, loading: authLoading } = useAuth();
  const [stats, setStats] = useState({});
  const [recentProblems, setRecentProblems] = useState([]);
  const [loading, setLoading] = useState(true);

  const config = roleDashboards[user?.role] || roleDashboards.citizen;

  const fetchStats = useCallback(async () => {
    try {
      const promises = config.stats.map((status) =>
        problemsApi.list({ status, limit: 1 }).then((res) => ({ status, count: res.data.length }))
      );
      const results = await Promise.all(promises);
      const statObj = {};
      results.forEach((r) => { statObj[r.status] = r.count; });
      setStats(statObj);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, [config]);

  const fetchRecentProblems = useCallback(async () => {
    try {
      const res = await problemsApi.list({ limit: 5 });
      setRecentProblems(res.data);
    } catch (err) {
      console.error('Failed to fetch recent problems:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authLoading) {
      // eslint-disable-next-line react/set-state-in-effect -- initial server data fetch
      fetchStats();
      // eslint-disable-next-line react/set-state-in-effect -- initial server data fetch
      fetchRecentProblems();
    }
  }, [authLoading, fetchStats, fetchRecentProblems]);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
      </div>
    );
  }

  const statusColors = {
    submitted: 'bg-gray-100 text-gray-800',
    validated: 'bg-blue-100 text-blue-800',
    categorized: 'bg-purple-100 text-purple-800',
    matched: 'bg-indigo-100 text-indigo-800',
    in_progress: 'bg-yellow-100 text-yellow-800',
    solution_proposed: 'bg-orange-100 text-orange-800',
    prototype: 'bg-pink-100 text-pink-800',
    pilot_test: 'bg-teal-100 text-teal-800',
    implemented: 'bg-green-100 text-green-800',
    closed: 'bg-gray-100 text-gray-600',
    rejected: 'bg-red-100 text-red-800',
    draft: 'bg-gray-100 text-gray-800',
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{config.title}</h1>
            <p className="text-gray-600">{config.subtitle}</p>
          </div>
          <Link
            to={config.primaryAction.path}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            {config.primaryAction.label}
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {config.stats.map((statKey) => (
            <div key={statKey} className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">{statKey.replace('_', ' ')}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">{stats[statKey] || 0}</p>
                </div>
                <div className={`p-3 rounded-full ${statusColors[statKey] || 'bg-gray-100 text-gray-800'}`}>
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6 border-b flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900">Recent Problems</h2>
            <Link to="/problems" className="text-sm text-blue-600 hover:underline">View All</Link>
          </div>
          <div className="divide-y">
            {loading ? (
              <div className="p-6 space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-1"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : recentProblems.length === 0 ? (
              <div className="p-12 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No problems yet</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Start by {user?.role === 'citizen' ? 'reporting a problem' : 'browsing available problems'}.
                </p>
              </div>
            ) : (
              recentProblems.map((problem) => (
                <Link
                  key={problem.id}
                  to={`/problems/${problem.id}`}
                  className="block p-6 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-gray-900">{problem.title}</h3>
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${statusColors[problem.status] || 'bg-gray-100 text-gray-800'}`}>
                          {problem.status.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-gray-600 text-sm line-clamp-1">{problem.description}</p>
                    </div>
                    <div className="text-right text-sm text-gray-500 whitespace-nowrap">
                      <p>{new Date(problem.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  );
}