import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { problemsApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Button, Card, CardContent, Badge, StatusBadge, PriorityBadge, Input, PageLoader } from '../components/ui';
import Navbar from '../components/Navbar';

const roleLabels = { citizen:'Citizen', student:'Student', faculty:'Faculty', university_admin:'University Admin', industry:'Industry', government:'Government', admin:'Admin' };

export default function ProblemDetail(){
  const { id } = useParams();
  const { user, loading: authLoading } = useAuth();
  const [problem,setProblem]=useState(null);
  const [solutions,setSolutions]=useState([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState('');
  const [showForm,setShowForm]=useState(false);
  const [form,setForm]=useState({title:'',description:'',approach:'',tech_stack:'',timeline:'',budget:''});
  const [submitting,setSubmitting]=useState(false);

  const fetchData=useCallback(async()=>{
    setLoading(true);
    try{
      const [p,s]=await Promise.all([problemsApi.get(id), problemsApi.solutions.list(id)]);
      setProblem(p.data); setSolutions(s.data);
    }catch(e){ setError(e.response?.data?.detail||'Failed to fetch'); }
    finally{ setLoading(false); }
  },[id]);

  // eslint-disable-next-line react/set-state-in-effect -- initial server data fetch
  useEffect(()=>{ if(!authLoading) fetchData(); },[authLoading,fetchData]);
  const canSolve = user && ['student','faculty','university_admin','industry','admin'].includes(user.role);
  const handleSubmit=async(e)=>{
    e.preventDefault(); setSubmitting(true);
    try{
      await problemsApi.solutions.create(id,{title:form.title,description:form.description,approach:form.approach,tech_stack:form.tech_stack.split(',').map(s=>s.trim()).filter(Boolean),estimated_timeline:form.timeline,estimated_budget:form.budget});
      setShowForm(false); setForm({title:'',description:'',approach:'',tech_stack:'',timeline:'',budget:''}); fetchData();
    }catch(e){ alert(e.response?.data?.detail||'Failed'); } finally{ setSubmitting(false); }
  };
  if(authLoading||loading) return <PageLoader />;
  if(error) return (<div className="min-h-screen bg-gray-50"><Navbar/><main className="max-w-3xl mx-auto px-4 py-12 text-center"><Card className="py-12"><h2 className="text-xl font-semibold">Problem Not Found</h2><p className="text-gray-600 mt-2">{error}</p><Link to="/problems" className="mt-6 inline-block"><Button>Back to Problems</Button></Link></Card></main></div>);
  if(!problem) return null;
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar/>
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link to="/problems" className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline mb-6">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7"/></svg> Back to Problems
        </Link>
        <Card className="overflow-hidden">
          <div className="h-1 bg-gradient-to-r from-indigo-600 to-purple-600"/>
          <CardContent>
            <div className="flex flex-wrap gap-2 mb-4">
              <StatusBadge status={problem.status}/>
              {problem.ai_priority && <PriorityBadge priority={problem.ai_priority}/>}
              {problem.ai_category && <Badge variant="purple">{problem.ai_category}</Badge>}
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">{problem.title}</h1>
            <div className="flex flex-wrap gap-4 text-sm text-gray-500 mb-6">
              <span>Submitted {new Date(problem.created_at).toLocaleDateString()} • {roleLabels[problem.submitter?.role]||'Unknown'}</span>
              <span className="font-mono text-xs">{problem.id}</span>
            </div>
            {problem.address && <div className="mb-6 p-4 bg-indigo-50 border border-indigo-100 rounded-lg flex gap-3"><svg className="w-5 h-5 text-indigo-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a2.998 2.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/></svg><div><p className="font-medium text-gray-900">Location</p><p className="text-gray-600 text-sm">{problem.address}</p>{problem.latitude&&<p className="text-xs text-gray-400">{problem.latitude.toFixed(4)}, {problem.longitude.toFixed(4)}</p>}</div></div>}
            {(problem.evidence_urls?.length||problem.evidence_text)&&<div className="mb-6"><h3 className="font-semibold text-gray-900 mb-2">Evidence</h3>{problem.evidence_urls?.map((u,i)=><a key={i} href={u} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline mr-4"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101"/></svg>Evidence {i+1}</a>)}{problem.evidence_text&&<div className="mt-3 p-4 bg-gray-50 rounded-lg border text-sm text-gray-700 whitespace-pre-wrap">{problem.evidence_text}</div>}</div>}
            <div className="prose max-w-none mb-6"><h3 className="font-semibold text-gray-900 mb-2">Description</h3><p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{problem.description}</p></div>
            {problem.tags?.length>0&&<div className="mb-4"><h3 className="font-semibold text-gray-900 mb-2">Tags</h3><div className="flex flex-wrap gap-2">{problem.tags.map(t=><Badge key={t} variant="outline">{t}</Badge>)}</div></div>}
            {problem.ai_tags?.length>0&&<div className="mb-4"><h3 className="font-semibold text-gray-900 mb-2">AI Tags</h3><div className="flex flex-wrap gap-2">{problem.ai_tags.map(t=><Badge key={t} variant="purple">{t}</Badge>)}</div></div>}
          </CardContent>
        </Card>
        <Card className="mt-6">
          <div className="p-6 border-b flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900">Solutions <span className="text-gray-500 font-normal">({solutions.length})</span></h2>
            {canSolve && !showForm && <Button variant="success" onClick={()=>setShowForm(true)}><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4"/></svg>Propose Solution</Button>}
          </div>
          {showForm&&<div className="p-6 border-b bg-emerald-50/50"><h3 className="font-semibold mb-4">Propose a Solution</h3><form onSubmit={handleSubmit} className="space-y-4">
            <Input label="Title *" value={form.title} onChange={e=>setForm({...form,title:e.target.value})} required/>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Description *</label><textarea value={form.description} onChange={e=>setForm({...form,description:e.target.value})} required rows={4} className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"/></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Approach</label><textarea value={form.approach} onChange={e=>setForm({...form,approach:e.target.value})} rows={3} className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"/></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4"><Input label="Tech Stack (comma)" value={form.tech_stack} onChange={e=>setForm({...form,tech_stack:e.target.value})} placeholder="React, Node"/><Input label="Timeline" value={form.timeline} onChange={e=>setForm({...form,timeline:e.target.value})} placeholder="3 months"/><Input label="Budget" value={form.budget} onChange={e=>setForm({...form,budget:e.target.value})} placeholder="50k INR"/></div>
            <div className="flex justify-end gap-3"><Button variant="secondary" onClick={()=>setShowForm(false)} type="button">Cancel</Button><Button type="submit" variant="success" loading={submitting}>Submit</Button></div>
          </form></div>}
          <div className="divide-y">
            {solutions.length===0?<div className="p-12 text-center"><div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3"><svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg></div><h3 className="font-medium text-gray-900">No solutions yet</h3><p className="text-sm text-gray-500">Be the first to propose a solution!</p></div>:solutions.map(s=>(
              <Link key={s.id} to={`/problems/${id}/solutions/${s.id}`} className="block p-6 hover:bg-gray-50">
                <h3 className="font-semibold text-gray-900">{s.title}</h3><p className="text-sm text-gray-600 line-clamp-2 mt-1">{s.description}</p>
                <div className="flex gap-2 mt-2 text-xs text-gray-500"><StatusBadge status={s.status} size="sm"/><span>{new Date(s.created_at).toLocaleDateString()}</span></div>
              </Link>
            ))}
          </div>
        </Card>
      </main>
    </div>
  );
}