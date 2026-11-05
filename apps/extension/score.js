const scoreButton = document.getElementById('score-frames');
const scoreResult = document.getElementById('score-result');
let scoreBatch = [], pendingScore;
function setScoreFrames(frames) {
  pendingScore?.abort();
  pendingScore = null;
  scoreBatch = frames;
  scoreButton.disabled = !frames.length;
  scoreResult.textContent = '';
}
scoreButton.addEventListener('click', async () => {
  if (!scoreBatch.length || pendingScore) return;
  const request = new AbortController();
  pendingScore = request;
  scoreButton.disabled = true;
  scoreResult.textContent = 'Reading the six frames on this Mac…';
  const timeout = setTimeout(() => request.abort(), 45000);
  try {
    const response = await fetch('http://127.0.0.1:8767/v1/score', {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-Uncanny-Client': 'popup'},
      body: JSON.stringify({frames: scoreBatch.map(f => f.data)}), signal: request.signal
    });
    if (!response.ok) throw new Error('Detector could not score these frames. Try capturing again.');
    const {signal, label, frames} = await response.json();
    if (pendingScore !== request) return;
    scoreResult.textContent = label + ' · ' + signal + '/100 median frame signal. Frame scores in capture order: ' + frames.join(', ') + '. This is not a probability.';
  } catch (error) {
    if (pendingScore === request) scoreResult.textContent = error instanceof TypeError || request.signal.aborted
      ? 'Local detector unavailable or timed out. Start detector/server.py on this Mac, then retry.'
      : error.message;
  } finally {
    clearTimeout(timeout);
    if (pendingScore === request) { pendingScore = null; scoreButton.disabled = false; }
  }
});
