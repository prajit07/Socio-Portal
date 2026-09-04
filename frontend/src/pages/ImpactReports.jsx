import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { governmentApi } from '../api/client';
import { Card, Button, Alert, PageLoader, StatCard } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);

function exportCSV(reports) {
  const headers = [
    'ID', 'Reported At', 'Beneficiaries', 'Impact Summary',
    'District', 'State', 'Proposal', 'Industry', 'Industry Type', 'Collab Stage',
  ];
  const rows = reports.map((r) => [
    r.id,
    r.reported_at ? new Date(r.reported_at).toLocaleDateString() : '—',
    r.beneficiaries_count ?? 0,
    `"${(r.impact_summary || '').replace(/"/g, '""')}"`,
    r.district || '—',
    r.state || '—',
    `"${(r.proposal_title || '').replace(/"/g, '""')}"`,
    `"${(r.industry_name || '').replace(/"/g, '""')}"`,
    r.industry_type || '—',
    r.collaboration_stage || '—',
  ]);

  const csv = [headers, ...rows].map((r) => r.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `socio-impact-reports-${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ImpactReports() {
  const { user } = useAuth();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    document.title = 'Impact Reports — Socio Connect';
    (async () => {
      setLoading(true);
      try {
        const res = await governmentApi.impactReports();
        setReports(asData(res) || []);
      } catch (e) {
        setError(e.response?.data?.detail || 'Failed to load impact reports.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (user?.role !== 'government') return <PageLoader />;
  if (loading) return <PageLoader />;

  const totalBeneficiaries = reports.reduce((s, r) => s + (r.beneficiaries_count || 0), 0);
  const districts = new Set(reports.map((r) => r.district).filter(Boolean)).size;

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1200px] px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-extrabold text-primary-navy">Social Impact Reports</h1>
            <p className="text-ink-soft mt-1">Exportable reports on societal outcomes across all collaborations.</p>
          </div>
          <div className="flex gap-3 flex-wrap">
            <Link to="/gov/dashboard" className="text-sm font-semibold text-primary hover:underline self-center">
              ← Dashboard
            </Link>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => window.print()}
            >
              🖨️ Print / Save PDF
            </Button>
            <Button
              size="sm"
              onClick={() => exportCSV(reports)}
              disabled={reports.length === 0}
            >
              📥 Export CSV
            </Button>
          </div>
        </div>

        {error && <Alert variant="danger" className="mb-6">{error}</Alert>}

        {/* KPI row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total Reports" value={reports.length} accent="primary" />
          <StatCard label="Total Beneficiaries" value={totalBeneficiaries.toLocaleString()} accent="success" />
          <StatCard label="Districts Covered" value={districts} accent="cyan" />
          <StatCard label="Industries Involved" value={new Set(reports.map((r) => r.industry_name).filter(Boolean)).size} accent="primary" />
        </div>

        {/* Reports table */}
        {reports.length === 0 ? (
          <Card className="text-center py-16">
            <div className="text-4xl mb-3">📋</div>
            <p className="text-ink-soft font-semibold">No impact reports filed yet.</p>
            <p className="text-sm text-ink-muted mt-1">Reports appear here when industry collaborations log social impact.</p>
          </Card>
        ) : (
          <>
            {/* Print-friendly summary */}
            <div className="hidden print:block mb-8 border-b pb-4">
              <h2 className="text-xl font-bold">Societal Innovation Portal — Impact Report Export</h2>
              <p className="text-sm text-gray-500 mt-1">Generated: {new Date().toLocaleString()}</p>
              <p className="text-sm text-gray-500">Total Beneficiaries: {totalBeneficiaries.toLocaleString()} | Reports: {reports.length}</p>
            </div>

            {/* Cards grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 print:grid-cols-2">
              {reports.map((r) => (
                <Card key={r.id} className="overflow-hidden">
                  <div className="h-1 bg-gradient-to-r from-emerald-500 to-teal-500" />
                  <div className="p-4">
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <div>
                        <p className="font-bold text-primary-navy text-sm line-clamp-1">
                          {r.proposal_title || 'Unnamed Proposal'}
                        </p>
                        <p className="text-xs text-ink-muted mt-0.5">
                          {r.industry_name || '—'} · {r.industry_type || '—'}
                        </p>
                      </div>
                      <span className="text-xs font-semibold rounded-full px-2 py-0.5 bg-emerald-100 text-emerald-700 whitespace-nowrap">
                        {r.collaboration_stage?.replace('_', ' ') || 'Unknown'}
                      </span>
                    </div>

                    {r.impact_summary && (
                      <p className="text-sm text-ink-soft mb-3 line-clamp-3 leading-relaxed">
                        {r.impact_summary}
                      </p>
                    )}

                    <div className="grid grid-cols-3 gap-2 text-center border-t border-line pt-3">
                      <div>
                        <div className="text-xl font-extrabold text-primary-navy">
                          {(r.beneficiaries_count || 0).toLocaleString()}
                        </div>
                        <div className="text-[10px] text-ink-muted uppercase tracking-wide">Beneficiaries</div>
                      </div>
                      <div>
                        <div className="text-sm font-bold text-primary-navy truncate">{r.district || '—'}</div>
                        <div className="text-[10px] text-ink-muted uppercase tracking-wide">District</div>
                      </div>
                      <div>
                        <div className="text-sm font-bold text-primary-navy truncate">{r.state || '—'}</div>
                        <div className="text-[10px] text-ink-muted uppercase tracking-wide">State</div>
                      </div>
                    </div>

                    <p className="text-[10px] text-ink-muted text-right mt-3">
                      Filed: {r.reported_at ? new Date(r.reported_at).toLocaleDateString() : '—'}
                    </p>
                  </div>
                </Card>
              ))}
            </div>
          </>
        )}
      </main>

      {/* Print-only styles */}
      <style>{`
        @media print {
          .no-print { display: none !important; }
          body { background: white; }
        }
      `}</style>
    </div>
  );
}
