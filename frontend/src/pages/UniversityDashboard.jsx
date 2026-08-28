import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { problemsApi, teamsApi, proposalsApi, universitiesApi } from '../api/client';
import { Button, Card, StatusBadge, Alert, PageLoader, TextArea } from '../components/ui';

const asData = (r) => (r && r.data !== undefined ? r.data : r);

export default function UniversityDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('problems');
  const [problems, setProblems] = useState([]);
  const [teams, setTeams] = useState([]);
  const [proposals, setProposals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState(null);
  const [students, setStudents] = useState([]);
  const [universityId, setUniversityId] = useState(null);
  const [studentResults, setStudentResults] = useState([]);
  const [bulkText, setBulkText] = useState('');
  const [sName, setSName] = useState('');
  const [sEmail, setSEmail] = useState('');
  const [sDept, setSDept] = useState('');
  const [sRoll, setSRoll] = useState('');
  const [sPw, setSPw] = useState('');

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [p, t, pr] = await Promise.all([
        problemsApi.list(),
        teamsApi.list(),
        proposalsApi.list(),
      ]);
      setProblems(asData(p) || []);
      setTeams(asData(t) || []);
      setProposals(asData(pr) || []);
      if (user?.role === 'university_admin') {
        const unis = asData(await universitiesApi.list()) || [];
        const uid = unis[0]?.id;
        setUniversityId(uid || null);
        if (uid) setStudents(asData(await universitiesApi.listStudents(uid)) || []);
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load dashboard.');
    } finally {
      setLoading(false);
    }
  };

  const loadStudents = async () => {
    if (!universityId) return;
    try { setStudents(asData(await universitiesApi.listStudents(universityId)) || []); }
    catch (e) { setError(e.response?.data?.detail || 'Failed to load students.'); }
  };

  const addBulk = async () => {
    const lines = bulkText.split('\n').map((l) => l.trim()).filter(Boolean);
    const items = [];
    for (const line of lines) {
      const parts = line.split(',').map((x) => x.trim());
      if (parts.length < 4) continue;
      items.push({ name: parts[0], email: parts[1], department: parts[2], roll_number: parts[3] });
    }
    if (items.length === 0) { setError('Enter one student per line: Name, email, Department, Roll Number'); return; }
    try {
      const res = await universitiesApi.addStudentsBulk(universityId, { students: items });
      setStudentResults(asData(res) || []);
      setBulkText('');
      await loadStudents();
      setError('');
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to add students.');
    }
  };

  const addSingle = async (e) => {
    e.preventDefault();
    if (!sName.trim() || !sEmail.trim() || !sDept.trim() || !sRoll.trim()) return;
    try {
      const res = await universitiesApi.addStudentsBulk(universityId, {
        students: [{ name: sName, email: sEmail, department: sDept, roll_number: sRoll, password: sPw || undefined }],
      });
      setStudentResults(asData(res) || []);
      setSName(''); setSEmail(''); setSDept(''); setSRoll(''); setSPw('');
      await loadStudents();
      setError('');
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to add student.');
    }
  };

  const handleApprove = async (id) => {
    setBusyId(id);
    try {
      await proposalsApi.approve(id);
      setProposals((prev) => prev.map((x) => (x.id === id ? { ...x, status: 'approved' } : x)));
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to approve proposal.');
    } finally {
      setBusyId(null);
    }
  };

  const handleFormTeam = () => {
    const firstId = problems[0]?.id;
    const pid = firstId || window.prompt('Enter a problem ID to form a team for:');
    navigate(pid ? `/university/teams/new?problemId=${pid}` : '/university/teams/new');
  };

  if (!['university_admin', 'student', 'faculty'].includes(user?.role)) return <PageLoader />;

  const tabs = [
    { id: 'problems', label: 'Problem Feed' },
    { id: 'teams', label: 'My Teams' },
    { id: 'proposals', label: 'My Proposals' },
    { id: 'approvals', label: 'Mentor Approvals' },
    ...(user?.role === 'university_admin' ? [{ id: 'students', label: 'Students' }] : []),
  ];

  const submitted = proposals.filter((p) => p.status === 'submitted');

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-extrabold text-primary-navy">
              University Workspace
            </h1>
            <p className="text-ink-soft mt-1">Collaborate on civic problems as {user?.role?.replace('_', ' ')}.</p>
          </div>
          <Button onClick={handleFormTeam}>Form Team</Button>
        </div>

        {error && <Alert variant="danger" className="mb-6">{error}</Alert>}

        <div className="flex flex-wrap gap-2 mb-6">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-btn text-sm font-semibold transition ${tab === t.id ? 'bg-primary text-white' : 'bg-white text-ink-soft border border-line'}`}
            >
              {t.label}
              {t.id === 'approvals' && submitted.length > 0 && (
                <span className="ml-2 rounded-full bg-tag-danger text-white text-xs px-2 py-0.5">{submitted.length}</span>
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <PageLoader />
        ) : tab === 'problems' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {problems.map((p) => (
              <Link key={p.id} to={`/problems/${p.id}`}>
                <Card hover>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-bold text-primary-navy line-clamp-2">{p.title}</h3>
                    <StatusBadge status={p.status} size="sm" />
                  </div>
                  <p className="text-sm text-ink-soft mt-2 line-clamp-3">{p.description}</p>
                  {p.ai_category && (
                    <span className="inline-block mt-2 text-[11px] font-semibold uppercase tracking-wide rounded-full bg-tag-blue/10 text-tag-blue px-2 py-0.5">
                      {p.ai_category}
                    </span>
                  )}
                </Card>
              </Link>
            ))}
          </div>
        ) : tab === 'teams' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {teams.map((t) => (
              <Link key={t.id} to={`/university/teams/${t.id}`}>
                <Card hover>
                  <h3 className="font-bold text-primary-navy">{t.name}</h3>
                  <p className="text-xs text-ink-muted mt-1">Problem: {t.problem_id}</p>
                </Card>
              </Link>
            ))}
            {teams.length === 0 && <Card className="text-center py-12 text-ink-soft">No teams yet.</Card>}
          </div>
        ) : tab === 'proposals' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {proposals.map((pr) => (
              <Link key={pr.id} to={`/university/proposals/${pr.id}`}>
                <Card hover>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-bold text-primary-navy line-clamp-2">{pr.title}</h3>
                    <StatusBadge status={pr.status} size="sm" />
                  </div>
                  <p className="text-xs text-ink-muted mt-1">Problem: {pr.problem_id}</p>
                </Card>
              </Link>
            ))}
            {proposals.length === 0 && <Card className="text-center py-12 text-ink-soft">No proposals yet.</Card>}
          </div>
        ) : tab === 'students' ? (
          <div className="space-y-6">
            {!universityId && <Card className="text-center py-12 text-ink-soft">No institute found. Create your institute first.</Card>}
            {universityId && (
              <>
                <Card>
                  <h2 className="font-bold text-primary-navy mb-3">Students ({students.length})</h2>
                  {students.length === 0 ? (
                    <p className="text-ink-soft">No students added yet.</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-ink-muted border-b border-line">
                            <th className="py-2">Name</th>
                            <th>Email</th>
                            <th>Department</th>
                            <th>Roll No.</th>
                            <th>Verified</th>
                          </tr>
                        </thead>
                        <tbody>
                          {students.map((s) => (
                            <tr key={s.id} className="border-b border-line">
                              <td className="py-2 font-semibold text-primary-navy">{s.name}</td>
                              <td>{s.email}</td>
                              <td>{s.department || '—'}</td>
                              <td>{s.roll_number || '—'}</td>
                              <td>{s.is_email_verified ? 'Yes' : 'No'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </Card>

                <Card>
                  <h2 className="font-bold text-primary-navy mb-1">Add Students in Bulk</h2>
                  <p className="text-xs text-ink-muted mb-3">One student per line: <span className="font-mono">Full Name, email, Department, Roll Number</span></p>
                  <TextArea rows={5} value={bulkText} onChange={(e) => setBulkText(e.target.value)} placeholder={"Alice, alice@uni.edu, CSE, 21CS01\nBob, bob@uni.edu, ECE, 21EC02"} />
                  <div className="mt-3">
                    <Button size="sm" onClick={addBulk}>Add Students</Button>
                  </div>
                </Card>

                <Card>
                  <h2 className="font-bold text-primary-navy mb-3">Add a Single Student</h2>
                  <form onSubmit={addSingle} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <Input label="Name" value={sName} onChange={(e) => setSName(e.target.value)} required />
                    <Input label="Email" type="email" value={sEmail} onChange={(e) => setSEmail(e.target.value)} required />
                    <Input label="Department" value={sDept} onChange={(e) => setSDept(e.target.value)} required />
                    <Input label="Roll Number" value={sRoll} onChange={(e) => setSRoll(e.target.value)} required />
                    <Input label="Password (optional)" value={sPw} onChange={(e) => setSPw(e.target.value)} placeholder="auto-generated if blank" />
                    <div className="flex items-end">
                      <Button type="submit" size="sm">Add Student</Button>
                    </div>
                  </form>
                </Card>

                {studentResults.length > 0 && (
                  <Card>
                    <h2 className="font-bold text-primary-navy mb-3">Created Credentials</h2>
                    <p className="text-xs text-ink-muted mb-2">Share these with students — passwords are shown only once.</p>
                    <div className="space-y-1 text-sm">
                      {studentResults.map((r, i) => (
                        <div key={i} className="border-b border-line pb-1">
                          <span className="font-semibold">{r.email}</span> — {r.status === 'created' ? `password: ${r.password}` : r.reason}
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
              </>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {submitted.map((pr) => (
              <Card key={pr.id} className="flex items-center justify-between gap-4">
                <div>
                  <Link to={`/university/proposals/${pr.id}`} className="font-bold text-primary-navy hover:underline">{pr.title}</Link>
                  <p className="text-xs text-ink-muted mt-1">Problem: {pr.problem_id}</p>
                </div>
                <Button size="sm" onClick={() => handleApprove(pr.id)} loading={busyId === pr.id}>Approve</Button>
              </Card>
            ))}
            {submitted.length === 0 && <Card className="text-center py-12 text-ink-soft">No proposals awaiting approval.</Card>}
          </div>
        )}
      </main>
    </div>
  );
}
