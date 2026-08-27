import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { problemsApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Button, Input, Select, Card, CardContent, Badge, StatusBadge, PriorityBadge, Alert, PageLoader, ListSkeleton } from '../components/ui';
import Navbar from '../components/Navbar';

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
};

const priorityColors = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
};

export default function ProblemList() {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    ai_category: '',
    ai_priority: '',
    page: 1,
  });

  useEffect(() => {
    if (!authLoading) fetchProblems();
  }, [authLoading, filters]);

  const fetchProblems = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await problemsApi.list({ ...filters, limit: 10 });
      setProblems(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch problems');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  };

  if (authLoading) return <PageLoader />;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {user?.role === 'citizen' ? 'My Problems' : 'All Problems'}
            </h1>
            <p className="text-gray-500 mt-1">
              {user?.role === 'citizen'
                ? 'Track and manage your submitted problems'
                : 'Browse and discover problems to solve'}
            </p>
          </div>
          {user?.role === 'citizen' && (
            <Link to="/problems/new">
              <Button size="lg">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Report New Problem
              </Button>
            </Link>
          )}
        </div>

        {error && (
          <Alert variant="danger" dismissible onDismiss={() => setError('')} className="mb-6">
            {error}
          </Alert>
        )}

        {/* Filters */}
        {user?.role !== 'citizen' && (
          <Card className="mb-6" padding="md">
            <div className="flex flex-wrap gap-4">
              <Select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                options={[
                  { value: '', label: 'All Statuses' },
                  { value: 'submitted', label: 'Submitted' },
                  { value: 'validated', label: 'Validated' },
                  { value: 'categorized', label: 'Categorized' },
                  { value: 'matched', label: 'Matched' },
                  { value: 'in_progress', label: 'In Progress' },
                  { value: 'solution_proposed', label: 'Solution Proposed' },
                  { value: 'prototype', label: 'Prototype' },
                  { value: 'pilot_test', label: 'Pilot Test' },
                  { value: 'implemented', label: 'Implemented' },
                  { value: 'closed', label: 'Closed' },
                  { value: 'rejected', label: 'Rejected' },
                ]}
              />
              <Input
                type="text"
                placeholder="AI Category"
                value={filters.ai_category}
                onChange={(e) => handleFilterChange('ai_category', e.target.value)}
              />
              <Select
                value={filters.ai_priority}
                onChange={(e) => handleFilterChange('ai_priority', e.target.value)}
                options={[
                  { value: '', label: 'All Priorities' },
                  { value: 'low', label: 'Low' },
                  { value: 'medium', label: 'Medium' },
                  { value: 'high', label: 'High' },
                  { value: 'critical', label: 'Critical' },
                ]}
              />
            </div>
          </Card>
        )}

        {/* Problems List */}
        {loading ? (
          <ListSkeleton count={5} />
        ) : problems.length === 0 ? (
          <Card className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No problems found</h3>
            <p className="mt-2 text-gray-500">
              {user?.role === 'citizen'
                ? 'Get started by reporting your first problem.'
                : 'No problems match your filters.'}
            </p>
            {user?.role === 'citizen' && (
              <Link to="/problems/new" className="mt-4 inline-block">
                <Button variant="primary">Report a Problem</Button>
              </Link>
            )}
          </Card>
        ) : (
          <div className="space-y-4">
            {problems.map((problem) => (
              <Link
                key={problem.id}
                to={`/problems/${problem.id}`}
                className="block"
              >
                <Card hover className="transition-all duration-200">
                  <CardContent>
                    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900 truncate pr-4">{problem.title}</h3>
                          <StatusBadge status={problem.status} />
                          {problem.ai_priority && <PriorityBadge priority={problem.ai_priority} />}
                          {problem.ai_category && (
                            <Badge variant="purple">{problem.ai_category}</Badge>
                          )}
                        </div>
                        <p className="text-gray-600 line-clamp-2">{problem.description}</p>
                        {problem.tags?.length && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {problem.tags.slice(0, 5).map((tag) => (
                              <Badge key={tag} variant="outline" size="sm">{tag}</Badge>
                            ))}
                            {problem.tags.length > 5 && (
                              <Badge variant="outline" size="sm">+{problem.tags.length - 5} more</Badge>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="text-right text-sm text-gray-500 whitespace-nowrap flex-shrink-0">
                        <p>Submitted: {new Date(problem.created_at).toLocaleDateString()}</p>
                        {problem.address && (
                          <p className="mt-1">
                            <svg className="inline w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            <span className="truncate block max-w-xs">{problem.address}</span>
                          </p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}