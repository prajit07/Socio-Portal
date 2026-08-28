import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import LocationPicker from '../components/LocationPicker';
import { useAuth } from '../context/AuthContext';
import { problemsApi, aiApi } from '../api/client';
import { transcribeAudio } from '../lib/puterSpeech';
import { Button, Input, TextArea, Card, Badge, Alert, PageLoader } from '../components/ui';

const STEPS = ['Describe', 'Evidence', 'Location', 'Review'];

function VoiceRecorder({ onRecordingReady }) {
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [transcribing, setTranscribing] = useState(false);
  const [error, setError] = useState('');
  const [targetLang, setTargetLang] = useState('English');
  const [translating, setTranslating] = useState(false);
  const [blobRef, setBlobRef] = useState(null);
  const mediaRef = useRef(null);
  const chunksRef = useRef([]);

  const start = async () => {
    setError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => chunksRef.current.push(e.data);
      mr.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        setBlobRef(blob);
        setTranscribing(true);
        let text = '';
        try {
          text = (await transcribeAudio(blob)) || '';
        } catch (e) {
          text = '';
        }
        setTranscript(text);
        setTranscribing(false);
        onRecordingReady(blob, 'voice_note.webm', text);
        stream.getTracks().forEach((t) => t.stop());
      };
      mediaRef.current = mr;
      mr.start();
      setRecording(true);
    } catch (e) {
      setError('Microphone access denied or unavailable. You can upload an audio file instead.');
    }
  };

  const stop = () => {
    mediaRef.current?.stop();
    setRecording(false);
  };

  const handleTranslate = async () => {
    if (!transcript) return;
    setTranslating(true);
    setError('');
    try {
      const res = await aiApi.translate(transcript, targetLang);
      const newText = `[Translated to ${targetLang}]: ${res.data.translated_text}\n\n[Original]: ${transcript}`;
      setTranscript(newText);
      onRecordingReady(blobRef, 'voice_note.webm', newText);
    } catch (e) {
      setError('Translation failed.');
    } finally {
      setTranslating(false);
    }
  };

  const languages = ['English', 'Hindi', 'Tamil', 'Telugu', 'Malayalam', 'Kannada', 'Marathi', 'Bengali'];

  return (
    <div className="border border-line rounded-card p-4 bg-bg-soft">
      <div className="flex items-center gap-3">
        <Button type="button" variant={recording ? 'danger' : 'secondary'} size="sm" onClick={recording ? stop : start}>
          {recording ? 'Stop Recording' : 'Start Voice Note'}
        </Button>
        {audioUrl && <audio controls src={audioUrl} className="h-8" />}
      </div>
      {transcribing && <p className="text-xs text-ink-muted mt-2">Transcribing with Puter…</p>}
      
      {transcript && (
        <div className="mt-3 rounded-card border border-line bg-white p-3 text-sm text-ink-soft">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-ink uppercase tracking-wide">Transcript</span>
            <div className="flex items-center gap-2">
              <select 
                value={targetLang} 
                onChange={(e) => setTargetLang(e.target.value)}
                className="text-xs border border-line rounded px-1.5 py-1 bg-bg-soft"
              >
                {languages.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
              <Button type="button" size="sm" variant="secondary" onClick={handleTranslate} loading={translating} disabled={translating}>
                Translate
              </Button>
            </div>
          </div>
          <p className="mt-1 whitespace-pre-wrap">{transcript}</p>
        </div>
      )}
      {error && <p className="text-xs text-tag-danger mt-2">{error}</p>}
    </div>
  );
}

export default function SubmitProblem() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({ title: '', description: '', tags: '', address: '', latitude: null, longitude: null });
  const [files, setFiles] = useState([]); // {file, kind, url, transcript, transcribing}
  const [voiceBlob, setVoiceBlob] = useState(null);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [position, setPosition] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const [tagExtracting, setTagExtracting] = useState(false);
  const [tagHint, setTagHint] = useState('');

  const update = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleExtractTags = async () => {
    if (!form.title.trim() && !form.description.trim()) {
      setTagHint('Please fill in a title and description first.');
      return;
    }
    setTagExtracting(true);
    setTagHint('');
    try {
      const res = await aiApi.extractTags(form.title, form.description, voiceTranscript);
      const rawTags = res.data?.tags || [];
      
      setForm((f) => {
        const existing = f.tags ? f.tags.split(',').map(s => s.trim()).filter(Boolean) : [];
        const extracted = rawTags.map((t) => t.name);
        const combined = [...new Set([...existing, ...extracted])];
        return { ...f, tags: combined.join(', ') };
      });
      
      setTagHint(`AI suggested ${rawTags.length} tag${rawTags.length !== 1 ? 's' : ''} · ${res.data?.category || ''} · Priority: ${res.data?.priority || ''}`);
    } catch (e) {
      setTagHint('Tag extraction failed. You can still type tags manually.');
    } finally {
      setTagExtracting(false);
    }
  };

  const addFiles = (list, kind) => {
    const arr = Array.from(list).map((file) => ({
      file,
      kind,
      url: URL.createObjectURL(file),
      transcript: null,
      transcribing: kind === 'audio',
    }));
    setFiles((prev) => [...prev, ...arr]);
    // Transcribe any audio uploads in-browser via Puter; backend STT is fallback.
    arr.forEach(async (entry) => {
      if (entry.kind !== 'audio') return;
      try {
        const text = await transcribeAudio(entry.file);
        setFiles((prev) => prev.map((f) => (f.file === entry.file ? { ...f, transcript: text, transcribing: false } : f)));
      } catch {
        setFiles((prev) => prev.map((f) => (f.file === entry.file ? { ...f, transcribing: false } : f)));
      }
    });
  };

  const onVoiceReady = (blob, _filename, transcript) => {
    setVoiceBlob(blob);
    setVoiceTranscript(transcript || '');
  };

  const submit = async () => {
    setLoading(true);
    setError('');
    try {
      const payload = {
        title: form.title,
        description: form.description,
        address: form.address || undefined,
        latitude: form.latitude ?? undefined,
        longitude: form.longitude ?? undefined,
        tags: form.tags ? form.tags.split(',').map((s) => s.trim()).filter(Boolean) : [],
      };
      const res = await problemsApi.create(payload);
      const problemId = res.data.id;
      setResult(res.data); // includes AI category / priority / status

      // Upload evidence (voice + files), forwarding any client-side transcript.
      const uploads = [];
      if (voiceBlob) uploads.push(problemsApi.uploadEvidence(problemId, voiceBlob, 'audio', voiceTranscript || undefined));
      for (const f of files) uploads.push(problemsApi.uploadEvidence(problemId, f.file, f.kind, f.transcript || undefined));
      await Promise.allSettled(uploads);

      setStep(4); // success screen
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to submit problem.');
    } finally {
      setLoading(false);
    }
  };

  if (user?.role !== 'citizen') return <PageLoader />;

  // Success screen (Step 4)
  if (step === 4 && result) {
    return (
      <div className="min-h-screen bg-bg-soft">
        <Navbar />
        <main className="mx-auto max-w-2xl px-4 py-12">
          <Card className="text-center py-10">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-tag-success/10 text-tag-success">
              <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
            </div>
            <h1 className="text-2xl font-extrabold text-primary-navy">Problem submitted!</h1>
            <p className="text-ink-soft mt-1">Our AI has processed your report.</p>
            <div className="mt-6 grid grid-cols-2 gap-3 text-left">
              <div className="rounded-card border border-line p-4">
                <div className="text-xs uppercase tracking-wide text-ink-muted">AI Category</div>
                <div className="font-semibold text-tag-blue mt-1">{result.ai_category || '—'}</div>
              </div>
              <div className="rounded-card border border-line p-4">
                <div className="text-xs uppercase tracking-wide text-ink-muted">Priority</div>
                <div className="font-semibold mt-1 capitalize text-primary-navy">{result.ai_priority || '—'}</div>
              </div>
              <div className="rounded-card border border-line p-4 col-span-2">
                <div className="text-xs uppercase tracking-wide text-ink-muted">Status</div>
                <div className="mt-1"><Badge color={result.status === 'duplicate' ? 'danger' : 'blue'}>{result.status}</Badge></div>
                {result.ai_duplicate_of && (
                  <p className="text-xs text-tag-warning mt-1">Flagged as duplicate of {result.ai_duplicate_of}</p>
                )}
              </div>
            </div>
            <div className="mt-6 flex justify-center gap-3">
              <Button onClick={() => navigate(`/problems/${result.id}`)}>Track this problem</Button>
              <Button variant="secondary" onClick={() => navigate('/citizen/dashboard')}>Go to Dashboard</Button>
            </div>
          </Card>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-soft">
      <Navbar />
      <main className="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-extrabold text-primary-navy">Report a Problem</h1>
          <p className="text-ink-soft mt-1">Step {step + 1} of 4 — {STEPS[step]}</p>
          <div className="mt-4 flex gap-2">
            {STEPS.map((s, i) => (
              <div key={s} className={`flex-1 h-1.5 rounded-full ${i <= step ? 'bg-primary' : 'bg-line'}`} />
            ))}
          </div>
        </div>

        {error && <Alert variant="danger" className="mb-4">{error}</Alert>}

        <Card>
          {step === 0 && (
            <div className="space-y-4">
              <Input label="Title *" name="title" value={form.title} onChange={update('title')} placeholder="Brief, descriptive title" required />
              <TextArea label="Description *" name="description" value={form.description} onChange={update('description')} rows={6} placeholder="What is the issue? Who is affected? How long has it persisted?" required />

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-semibold text-ink">Tags (optional, comma separated)</label>
                  <button
                    type="button"
                    onClick={handleExtractTags}
                    disabled={tagExtracting || (!form.title.trim() && !form.description.trim())}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 text-white text-xs font-bold hover:opacity-90 transition disabled:opacity-50 shadow-sm"
                  >
                    {tagExtracting ? (
                      <>
                        <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Extracting…
                      </>
                    ) : (
                      <>
                        <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                        ✨ Extract Tags with AI
                      </>
                    )}
                  </button>
                </div>
                <Input name="tags" value={form.tags} onChange={update('tags')} placeholder="water, sanitation, health" hint="Keywords help AI categorization." />
                
                {tagHint && (
                  <p className="text-xs mt-2 px-3 py-1.5 rounded-lg bg-violet-50 border border-violet-200 text-violet-700 font-medium">
                    {tagHint}
                  </p>
                )}
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-ink mb-1.5">Voice note</label>
                <VoiceRecorder onRecordingReady={onVoiceReady} />
                <p className="text-xs text-ink-muted mt-2">Speech is transcribed in your browser with Puter (free). You may be asked to sign in to Puter on first use.</p>
              </div>
              <div>
                <label className="block text-sm font-semibold text-ink mb-1.5">Upload evidence</label>
                <input
                  type="file"
                  multiple
                  accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.txt"
                  onChange={(e) => addFiles(e.target.files, e.target.files[0]?.type.startsWith('image') ? 'image' : e.target.files[0]?.type.startsWith('video') ? 'video' : e.target.files[0]?.type.startsWith('audio') ? 'audio' : 'document')}
                  className="block w-full text-sm text-ink-soft file:mr-3 file:rounded-btn file:border-0 file:bg-primary file:px-4 file:py-2 file:text-white file:font-semibold"
                />
                {files.length > 0 && (
                  <ul className="mt-3 space-y-2">
                    {files.map((f, i) => (
                      <li key={i} className="border border-line rounded-card px-3 py-2 text-sm">
                        <div className="flex items-center justify-between">
                          <span className="truncate">{f.file.name}</span>
                          <Badge variant="outline">{f.kind}</Badge>
                        </div>
                        {f.kind === 'audio' && f.transcribing && (
                          <p className="text-xs text-ink-muted mt-1">Transcribing with Puter…</p>
                        )}
                        {f.kind === 'audio' && f.transcript && (
                          <p className="text-xs text-ink-soft mt-1 italic">“{f.transcript}”</p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}

          {step === 2 && (
            <LocationPicker
              position={position}
              setPosition={(p) => { setPosition(p); setForm((f) => ({ ...f, latitude: p[0], longitude: p[1] })); }}
              address={form.address}
              setAddress={(v) => setForm((f) => ({ ...f, address: v }))}
            />
          )}

          {step === 3 && (
            <div className="space-y-3 text-sm">
              <div><span className="font-semibold text-primary-navy">Title:</span> {form.title}</div>
              <div><span className="font-semibold text-primary-navy">Description:</span> <span className="text-ink-soft">{form.description}</span></div>
              <div><span className="font-semibold text-primary-navy">Tags:</span> {form.tags || '—'}</div>
              <div><span className="font-semibold text-primary-navy">Evidence:</span> {files.length + (voiceBlob ? 1 : 0)} file(s)</div>
              <div><span className="font-semibold text-primary-navy">Location:</span> {form.address || (position ? `${position[0].toFixed(4)}, ${position[1].toFixed(4)}` : '—')}</div>
              <Alert variant="info">On submit, our AI will categorize, score priority, check for duplicates and route your problem to relevant universities & industry partners.</Alert>
            </div>
          )}

          <div className="mt-6 flex justify-between">
            <Button variant="ghost" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}>
              Back
            </Button>
            {step < 3 ? (
              <Button onClick={() => setStep((s) => s + 1)} disabled={step === 0 && (!form.title || !form.description)}>
                Next
              </Button>
            ) : (
              <Button onClick={submit} loading={loading}>Submit Problem</Button>
            )}
          </div>
        </Card>
      </main>
    </div>
  );
}
