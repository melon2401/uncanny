const scoreButton = document.getElementById('score-frames');
const scoreResult = document.getElementById('score-result');
let scoreBatch = [], pendingScore, lastResult = null, captureMode = 'stills';
function setScoreFrames(frames, mode = 'stills') {
  pendingScore?.abort();
  pendingScore = null;
  scoreBatch = frames;
  captureMode = mode;
  lastResult = null;
  document.getElementById("save-sample").disabled = !frames.length;
  scoreButton.disabled = !frames.length;
  scoreButton.hidden = true;
  scoreResult.textContent = '';
}
async function scoreFrames() {
  if (captureMode === 'motion' || !scoreBatch.length || pendingScore) return;
  const request = new AbortController();
  pendingScore = request;
  scoreButton.disabled = true;
  scoreButton.hidden = true;
  scoreResult.textContent = 'Reading the six frames on this Mac…';
  const timeout = setTimeout(() => request.abort(), 45000);
  try {
    const response = await fetch('http://127.0.0.1:8767/v1/score', {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-Uncanny-Client': 'popup'},
      body: JSON.stringify({frames: scoreBatch.map(f => f.data)}), signal: request.signal
    });
    if (!response.ok) throw new Error('Detector could not score these frames. Try capturing again.');
    const result = await response.json();
    const {signal, label, frames} = result;
    if (pendingScore !== request) return;
    lastResult = result;
    document.getElementById('headline').textContent = 'Analysis complete.';
    document.getElementById('status').textContent = 'Six frames checked on this Mac.';
    scoreResult.textContent = label + ' · ' + signal + '/100' + (label === 'Inconclusive' ? (result.reason === 'conflicting_frames' ? ' — Frames disagree.' : result.reason === 'repeated_frames' ? ' — Too few distinct frames.' : ' — No reliable conclusion.') : ' — Signal across the sampled frames.');
    scoreBatch.forEach((frame, index) => {
      const caption = document.getElementById('frames').children[index]?.children[1];
      if (caption) caption.textContent = frame.time.toFixed(1) + 's · ' + frames[index] + '/100';
    });
  } catch (error) {
    if (pendingScore === request) {
      scoreButton.hidden = false;
      scoreButton.textContent = 'Retry analysis';
      document.getElementById('headline').textContent = 'Frames saved. Try again.';
      scoreResult.textContent = error instanceof TypeError || request.signal.aborted
      ? 'Local detector unavailable or timed out. Start detector/server.py on this Mac, then retry.'
      : error.message;
    }
  } finally {
    clearTimeout(timeout);
    if (pendingScore === request) { pendingScore = null; scoreButton.disabled = false; }
  }
}
scoreButton.addEventListener('click', scoreFrames);

document.getElementById('save-sample').addEventListener('click', () => {
  if (!scoreBatch.length) return;
  const source = new URL(targetTab.url); source.search = ''; source.hash = '';
  const sample = {schema: captureMode === 'motion' ? 2 : 1, mode: captureMode, targetIntervalMs: captureMode === 'motion' ? 125 : 1100, source: source.href, label: document.getElementById('known-label').value,
    capturedAt: new Date().toISOString(), result: lastResult, frames: scoreBatch};
  const url = URL.createObjectURL(new Blob([JSON.stringify(sample)], {type: 'application/json'}));
  const link = document.createElement('a'); link.href = url;
  link.download = (captureMode === 'motion' ? 'uncanny-motion-' : 'uncanny-sample-') + Date.now() + '.json'; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
