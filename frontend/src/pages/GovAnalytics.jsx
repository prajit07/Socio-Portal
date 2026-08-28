import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, AreaChart, Area, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { governmentApi } from '../api/client';
import { Card, StatCard, Alert, PageLoader } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);

const COLORS = [
  '#1E5EFF', '#22C7F2', '#1B9C68', '#F59E0B', '#D64550', '#8B5CF6',
  '#EC4899', '#06B6D4', '#10B981', '#F97316', '#6366F1', '#EF4444',
];

const STATUS_COLORS = {
  pending_validation: '#8A94A6', validated: '#1E5EFF', open: '#1E5EFF',
  in_review: '#0B2545', proposal_submitted: '#0B2545', in_collaboration: '#22C7F2',
  prototype: '#22C7F2', pilot: '#1B9C68', implemented: '#1B9C68', closed: '#8A94A6',
  duplicate: '#D64550', rejected: '#D64550',
};

const PRIORITY_COLORS = { low: '#8A94A6', medium: '#F59E0B', high: '#F97316', critical: '#D64550' };

export default function GovAnalytics() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await governmentApi.analytics();
        setData(asData(res));
      } catch (e) {
        setError(e.response?.data?.detail || 'Failed to load analytics.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (user?.role !== 'government') return <PageLoader />;
  if (loading) return <PageLoader />;

  const k = data?.kpis || {};
  const statusData = (data?.by_status || []).map((x) => ({ name: x.status.replace(/_/g, ' '), value: x.count }));
  const categoryData = (data?.by_category || []).map((x) => ({ name: x.category, count: x.count }));
  const priorityData = (data?.by_priority || []).map((x) => ({ name: x.priority, count: x.count, fill: PRIORITY_COLORS[x.priority] || '#ccc' }));
  const districtData = data?.by_district || [];
  const monthlyData = data?.monthly_trends || [];
  const catTrends = data?.category_trends || [];
  const collabStages = data?.collaboration_stages || [];

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1400px] px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-extrabold text-primary-navy">Analytics Dashboard</h1>
            <p className="text-ink-soft mt-1">Deep insights into societal innovation activity across all sectors.</p>
          </div>
          <div className="flex gap-3">
            <Link to="/gov/dashboard" className="text-sm font-semibold text-primary hover:underline">← KPI Dashboard</Link>
            <Link to="/problems" className="text-sm font-semibold text-primary hover:underline">View Problems →</Link>
          </div>
        </div>

        {error && <Alert variant="danger" className="mb-6">{error}</Alert>}

        {/* KPI Row */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <StatCard label="Total Problems" value={k.total_problems || 0} accent="primary" />
          <StatCard label="Resolved" value={k.resolved || 0} accent="success" />
          <StatCard label="Completion Rate" value={`${k.completion_rate || 0}%`} accent="primary" />
          <StatCard label="Beneficiaries" value={(k.total_beneficiaries || 0).toLocaleString()} accent="cyan" />
          <StatCard label="Impact Reports" value={k.impact_reports || 0} accent="success" />
        </div>

        {/* Row 1: Monthly Trends + Status Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <Card className="lg:col-span-2">
            <h2 className="font-bold text-primary-navy mb-4">Monthly Problem Submissions</h2>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Area type="monotone" dataKey="count" stroke="#1E5EFF" fill="#1E5EFF" fillOpacity={0.15} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </Card>

          <Card>
            <h2 className="font-bold text-primary-navy mb-4">Status Breakdown</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                  style={{ fontSize: '11px' }}
                >
                  {statusData.map((entry, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </div>

        {/* Row 2: District-wise + Category bar */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card>
            <h2 className="font-bold text-primary-navy mb-4">Problems by District</h2>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={districtData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis type="category" dataKey="district" tick={{ fontSize: 11 }} width={120} />
                <Tooltip />
                <Bar dataKey="count" fill="#1E5EFF" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card>
            <h2 className="font-bold text-primary-navy mb-4">Problems by Category</h2>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={categoryData} margin={{ left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={80} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {categoryData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>

        {/* Row 3: Priority + Category Trends */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <Card>
            <h2 className="font-bold text-primary-navy mb-4">Priority Distribution</h2>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={priorityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {priorityData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card className="lg:col-span-2">
            <h2 className="font-bold text-primary-navy mb-4">Category Trends (6 months)</h2>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} allowDuplicatedCategory={false} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                {catTrends.map((ct, i) => (
                  <Line
                    key={ct.category}
                    type="monotone"
                    data={ct.data}
                    dataKey="count"
                    name={ct.category}
                    stroke={COLORS[i % COLORS.length]}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </div>

        {/* Row 4: Collaboration Stages + Completion */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card>
            <h2 className="font-bold text-primary-navy mb-4">Collaboration Stages</h2>
            {collabStages.length === 0 ? (
              <p className="text-ink-soft text-center py-8">No active collaborations.</p>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={collabStages.map((s) => ({ stage: s.stage.replace(/_/g, ' '), count: s.count }))}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="stage" tick={{ fontSize: 11 }} />
                  <PolarRadiusAxis tick={{ fontSize: 10 }} />
                  <Radar name="Collaborations" dataKey="count" stroke="#1E5EFF" fill="#1E5EFF" fillOpacity={0.3} />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </Card>

          <Card>
            <h2 className="font-bold text-primary-navy mb-4">Completion Funnel</h2>
            <div className="space-y-3 mt-4">
              {[
                { label: 'Total Submitted', value: k.total_problems || 0, color: '#1E5EFF' },
                { label: 'Open / In Review', value: k.open || 0, color: '#22C7F2' },
                { label: 'Proposals', value: k.proposals || 0, color: '#8B5CF6' },
                { label: 'Active Collaborations', value: k.active_collaborations || 0, color: '#F59E0B' },
                { label: 'Resolved', value: k.resolved || 0, color: '#1B9C68' },
              ].map((item) => {
                const pct = k.total_problems ? Math.round((item.value / k.total_problems) * 100) : 0;
                return (
                  <div key={item.label}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="font-semibold text-primary-navy">{item.label}</span>
                      <span className="text-ink-muted">{item.value} ({pct}%)</span>
                    </div>
                    <div className="h-3 rounded-full bg-bg-soft overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{ width: `${pct}%`, backgroundColor: item.color }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}
