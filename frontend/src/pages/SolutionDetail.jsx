import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { problemsApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Button, Card, CardContent, Badge, StatusBadge, Input, Select, PageLoader } from '../components/ui';
import Navbar from '../components/Navbar';

const roleLabels={ citizen:'Citizen', student:'Student', faculty:'Faculty', university_admin:'University Admin', industry:'Industry', government:'Government', admin:'Admin' };

export default function SolutionDetail(){
  const { problemId, solutionId }=useParams();
  const { user, loading: authLoading }=useAuth();
  const [solution,setSolution]=useState(null); const [loading,setLoading]=useState(true); const [error,setError]=useState(''); const [editing,setEditing]=useState(false); const [editData,setEditData]=useState({});
  useEffect(()=>{ if(!authLoading) fetchData(); },[authLoading]);
  const fetchData=async()=>{ setLoading(true); try{ const r=await problemsApi.solutions.get(problemId,solutionId); setSolution(r.data); setEditData(r.data);}catch(e){ setError(e.response?.data?.detail||'Failed'); } finally{ setLoading(false); }};
  const handleUpdate=async e=>{ e.preventDefault(); try{ const d={...editData,tech_stack:typeof editData.tech_stack==='string'?editData.tech_stack.split(',').map(s=>s.trim()).filter(Boolean):editData.tech_stack}; await problemsApi.solutions.update(problemId,solutionId,d); setEditing(false); fetchData(); }catch(e){ alert(e.response?.data?.detail||'Failed'); } };
  const canEdit=user&&(solution?.author_id===user.id||['admin','government','university_admin','faculty'].includes(user.role));
  if(authLoading||loading) return <PageLoader/>;
  if(error||!solution) return (<div className="min-h-screen bg-gray-50"><Navbar/><main className="max-w-3xl mx-auto px-4 py-12 text-center"><Card className="py-12"><h2 className="text-xl font-semibold">Solution Not Found</h2><Link to={`/problems/${problemId}`} className="mt-4 inline-block"><Button>Back</Button></Link></Card></main></div>);
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar/>
      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link to={`/problems/${problemId}`} className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline mb-6"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7"/></svg>Back to Problem</Link>
        <Card className="overflow-hidden">
          <div className="h-1 bg-gradient-to-r from-emerald-500 to-teal-500"/>
          <div className="p-6 border-b flex justify-between items-start">
            <div><h1 className="text-2xl font-bold text-gray-900">{solution.title}</h1><div className="flex gap-2 mt-2"><StatusBadge status={solution.status}/><Badge variant="outline">{roleLabels[solution.author?.role]||'Unknown'}</Badge></div></div>
            {canEdit&&!editing&&<Button onClick={()=>setEditing(true)}>Edit</Button>}
          </div>
          <CardContent>
            {editing?(
              <form onSubmit={handleUpdate} className="space-y-4">
                <Input label="Title *" value={editData.title} onChange={e=>setEditData({...editData,title:e.target.value})} required/>
                <div><label className="block text-sm font-medium mb-1">Description *</label><textarea value={editData.description} onChange={e=>setEditData({...editData,description:e.target.value})} required rows={4} className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"/></div>
                <div><label className="block text-sm font-medium mb-1">Approach</label><textarea value={editData.approach} onChange={e=>setEditData({...editData,approach:e.target.value})} rows={3} className="w-full px-4 py-2.5 rounded-lg border"/></div>
                <div className="grid grid-cols-2 gap-4"><Input label="Tech Stack" value={Array.isArray(editData.tech_stack)?editData.tech_stack.join(', '):editData.tech_stack} onChange={e=>setEditData({...editData,tech_stack:e.target.value})}/><Select label="Status" value={editData.status} onChange={e=>setEditData({...editData,status:e.target.value})} options={[{value:'draft',label:'Draft'},{value:'submitted',label:'Submitted'},{value:'under_review',label:'Under Review'},{value:'accepted',label:'Accepted'},{value:'rejected',label:'Rejected'},{value:'prototype',label:'Prototype'},{value:'pilot',label:'Pilot'},{value:'implemented',label:'Implemented'}]}/></div>
                <div className="grid grid-cols-2 gap-4"><Input label="Timeline" value={editData.estimated_timeline||''} onChange={e=>setEditData({...editData,estimated_timeline:e.target.value})}/><Input label="Budget" value={editData.estimated_budget||''} onChange={e=>setEditData({...editData,estimated_budget:e.target.value})}/></div>
                <Input label="GitHub URL" value={editData.github_url||''} onChange={e=>setEditData({...editData,github_url:e.target.value})}/>
                <Input label="Demo URL" value={editData.demo_url||''} onChange={e=>setEditData({...editData,demo_url:e.target.value})}/>
                <div className="flex justify-end gap-3"><Button variant="secondary" type="button" onClick={()=>setEditing(false)}>Cancel</Button><Button type="submit">Save</Button></div>
              </form>
            ):(
              <div className="space-y-6">
                <div><h3 className="font-semibold mb-2">Description</h3><p className="text-gray-700 whitespace-pre-wrap">{solution.description}</p></div>
                {solution.approach&&<div><h3 className="font-semibold mb-2">Approach</h3><p className="text-gray-700 whitespace-pre-wrap">{solution.approach}</p></div>}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  {solution.tech_stack?.length>0&&<div className="col-span-2"><p className="text-gray-500">Tech Stack</p><div className="flex flex-wrap gap-1 mt-1">{solution.tech_stack.map(t=><Badge key={t} variant="outline" size="sm">{t}</Badge>)}</div></div>}
                  {solution.estimated_timeline&&<div><p className="text-gray-500">Timeline</p><p className="font-medium">{solution.estimated_timeline}</p></div>}
                  {solution.estimated_budget&&<div><p className="text-gray-500">Budget</p><p className="font-medium">{solution.estimated_budget}</p></div>}
                </div>
                <div className="flex gap-2">
                  {solution.github_url&&<a href={solution.github_url} target="_blank" rel="noopener noreferrer"><Button variant="secondary" size="sm">GitHub</Button></a>}
                  {solution.demo_url&&<a href={solution.demo_url} target="_blank" rel="noopener noreferrer"><Button size="sm">Live Demo</Button></a>}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}