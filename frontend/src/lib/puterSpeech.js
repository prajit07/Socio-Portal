// Browser-side speech-to-text via Puter.js (free, keyless, user-pays model).
// Puter runs entirely client-side, so transcripts are produced in the browser
// and sent to our backend as plain text. If Puter isn't available or the call
// fails, we return null and let the backend fall back to server-side STT.
export async function transcribeAudio(blob) {
  if (typeof window === 'undefined' || !window.puter?.ai?.speech2txt) {
    return null;
  }
  try {
    const result = await window.puter.ai.speech2txt(blob, { model: 'whisper-1' });
    if (!result) return null;
    return typeof result === 'string' ? result : result.text || null;
  } catch (e) {
    console.warn('Puter speech-to-text failed; backend STT will be used.', e);
    return null;
  }
}
