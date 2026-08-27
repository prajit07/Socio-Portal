import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { problemsApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Button, Input, Card, Alert } from '../components/ui';
import Navbar from '../components/Navbar';

export default function ProblemSubmit(){
  const navigate=useNavigate();
  const { user, loading: authLoading }=useAuth();
  const [form,setForm]=useState({title:'',description:'',evidence_urls:'',evidence_text:'',latitude:'',longitude:'',address:'',tags:''});
  const [error,setError]=useState(''); const [loading,setLoading]=useState(false);
  if(authLoading) return <div className="min-h-screen flex items-center justify-center"><div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"/></div>;
  if(!user||user.role!=='citizen') return (<div className="min-h-screen bg-gray-50"><Navbar/><main className="max-w-2xl mx-auto px-4 py-12 text-center"><Card className="py-12"><h2 className="text-xl font-semibold">Access Denied</h2><p className="text-gray-600">Only citizens can submit problems.</p><Button className="mt-6" onClick={()=>navigate('/')}>Go Home</Button></Card></main></div>);
  const handleChange=e=>setForm({...form,[e.target.name]:e.target.value});
  const handleSubmit=async e=>{
    e.preventDefault(); setError(''); setLoading(true);
    try{
      const data={title:form.title,description:form.description,evidence_urls:form.evidence_urls.split(',').map(s=>s.trim()).filter(Boolean),evidence_text:form.evidence_text||undefined,latitude:form.latitude?parseFloat(form.latitude):undefined,longitude:form.longitude?parseFloat(form.longitude):undefined,address:form.address||undefined,tags:form.tags.split(',').map(s=>s.trim()).filter(Boolean)};
      const res=await problemsApi.create(data); navigate(`/problems/${res.data.id}`);
    }catch(err){ setError(err.response?.data?.detail||'Failed'); } finally{ setLoading(false); }
  };
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar/>
      <main className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Report a Problem</h1>
          <p className="text-gray-500">Submit a societal issue with evidence and location</p>
        </div>
        {error&&<Alert variant="danger" className="mb-6">{error}</Alert>}
        <Card>
          <form onSubmit={handleSubmit} className="space-y-5 p-1">
            <Input label="Title *" name="title" value={form.title} onChange={handleChange} required maxLength={200} placeholder="Brief, descriptive title"/>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Description *</label><textarea name="description" value={form.description} onChange={handleChange} required rows={5} placeholder="What is the issue? Where? How does it affect people?" className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"/></div>
            <Input label="Evidence URLs (comma separated)" name="evidence_urls" value={form.evidence_urls} onChange={handleChange} placeholder="https://example.com/photo.jpg, https://example.com/video.mp4" hint="Links to photos, videos, voice recordings"/>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Evidence Text / Transcript</label><textarea name="evidence_text" value={form.evidence_text} onChange={handleChange} rows={3} placeholder="Transcribed voice recording" className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"/></div>
            <div className="grid grid-cols-2 gap-4"><Input label="Latitude" name="latitude" type="number" step="any" value={form.latitude} onChange={handleChange} placeholder="28.6139"/><Input label="Longitude" name="longitude" type="number" step="any" value={form.longitude} onChange={handleChange} placeholder="77.2090"/></div>
            <Input label="Address" name="address" value={form.address} onChange={handleChange} placeholder="Community Park, Sector 12, Dwarka, New Delhi"/>
            <Input label="Tags (comma separated)" name="tags" value={form.tags} onChange={handleChange} placeholder="garbage, park, sanitation" hint="Keywords: waste, water, traffic, education..."/>
            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button variant="secondary" onClick={()=>navigate('/problems')} type="button">Cancel</Button>
              <Button type="submit" loading={loading}>Submit Problem</Button>
            </div>
          </form>
        </Card>
      </main>
    </div>
  );
}