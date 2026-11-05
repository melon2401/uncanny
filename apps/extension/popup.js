const platformName = document.getElementById('platform-name');
const button = document.getElementById('analyze-button');
const scanner = document.getElementById('scanner');
const headline = document.getElementById('headline');
const status = document.getElementById('status');
const activity = document.getElementById('activity');
const gallery = document.getElementById('frames');
const results = document.getElementById('capture-results');
let activeJob = null;
let targetTab;

function checkCancelled(job) {
  if (job.cancelled) throw new Error('Capture cancelled. Partial frames were discarded.');
}
async function assertSameTab(job) {
  checkCancelled(job);
  const [tab] = await chrome.tabs.query({ active: true, windowId: targetTab.windowId });
  if (tab?.id !== targetTab.id || tab.url !== targetTab.url) throw new Error('The active page changed. Return to the video and reopen Uncanny.');
}
async function readFrame(job) {
  await assertSameTab(job);
  const [reply] = await chrome.scripting.executeScript({ target: { tabId: targetTab.id }, func: sampleVideo, args: [job.id, targetTab.url] });
  checkCancelled(job);
  if (!reply?.result) throw new Error('Could not read the video. Reload the page and try again.');
  const frame = reply.result;
  if (frame.data) return frame;
  await assertSameTab(job);
  const screenshot = await chrome.tabs.captureVisibleTab(targetTab.windowId, { format: 'png' });
  await assertSameTab(job);
  const [verification] = await chrome.scripting.executeScript({
    target: { tabId: targetTab.id },
    func: (id) => {
      const state = globalThis.__uncannyFrameSession;
      if (!state || state.session !== id || !state.video.isConnected) return null;
      const r = state.video.getBoundingClientRect();
      return { source: state.video.currentSrc, page: location.href, width: innerWidth, height: innerHeight, r: { left: r.left, top: r.top, width: r.width, height: r.height } };
    }, args: [job.id]
  });
  const v = verification?.result;
  if (!v || v.source !== frame.source || v.page !== frame.page || v.width !== frame.viewport.width || v.height !== frame.viewport.height ||
      Object.keys(frame.element).some(key => Math.abs(v.r[key] - frame.element[key]) > 2)) {
    throw new Error('The video moved during capture. Keep the page still and try again.');
  }
  const image = new Image(); image.src = screenshot; await image.decode();
  checkCancelled(job);
  const rect = cropBounds(frame, image.naturalWidth, image.naturalHeight);
  const scale = Math.min(1, 720 / Math.max(rect.width, rect.height));
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(rect.width * scale); canvas.height = Math.round(rect.height * scale);
  canvas.getContext('2d').drawImage(image, rect.x, rect.y, rect.width, rect.height, 0, 0, canvas.width, canvas.height);
  frame.data = canvas.toDataURL('image/jpeg', 0.9);
  return frame;
}
function showFrames(frames) {
  gallery.replaceChildren();
  frames.forEach((frame, index) => {
    const figure = document.createElement('figure'), img = document.createElement('img'), caption = document.createElement('figcaption');
    img.src = frame.data; img.alt = `Captured video frame ${index + 1} at ${frame.time.toFixed(1)} seconds`;
    caption.textContent = `${index + 1} · ${frame.time.toFixed(1)}s`;
    figure.append(img, caption); gallery.append(figure);
  });
  document.getElementById('capture-note').textContent = frames.some(f => f.method === 'Visible video crop')
    ? 'Captured from the visible player. In-player text or controls may appear. No AI analysis yet.'
    : 'Captured directly from the video pixels. No AI analysis yet.';
  results.hidden = false;
}
async function capture() {
  const job = { id: crypto.randomUUID(), cancelled: false }; activeJob = job;
  gallery.replaceChildren(); results.hidden = true;
  scanner.classList.add('is-scanning'); activity.classList.add('active'); button.classList.add('cancel');
  button.textContent = 'Cancel capture'; headline.textContent = 'Looking closer…';
  const frames = [];
  try {
    for (let i = 0; i < 6; i++) {
      if (i) await new Promise(resolve => setTimeout(resolve, 1100));
      checkCancelled(job);
      status.textContent = `Capturing frame ${i + 1} of 6. Keep this popup open and the video playing.`;
      frames.push(await readFrame(job));
    }
    checkCancelled(job); showFrames(frames);
    headline.textContent = 'Six frames captured.';
    status.textContent = 'Check the thumbnails below. Nothing has been uploaded or scored.';
  } catch (error) {
    gallery.replaceChildren(); results.hidden = true;
    headline.textContent = job.cancelled ? 'Capture cancelled.' : 'Could not capture.';
    status.textContent = error.message || 'Capture failed. Reopen Uncanny and try again.';
  } finally {
    activeJob = null;
    scanner.classList.remove('is-scanning'); activity.classList.remove('active'); button.classList.remove('cancel');
    button.textContent = 'Capture frames'; button.disabled = false;
  }
}
button.addEventListener('click', () => {
  if (activeJob) { activeJob.cancelled = true; button.disabled = true; button.textContent = 'Cancelling…'; }
  else capture();
});
document.getElementById('clear-frames').addEventListener('click', () => {
  gallery.replaceChildren(); results.hidden = true; headline.textContent = 'Frames cleared.';
  status.textContent = 'Play a video, then capture again when ready.';
});
window.addEventListener('pagehide', () => { if (activeJob) activeJob.cancelled = true; });
async function initialize() {
  button.disabled = true;
  if (!globalThis.chrome?.scripting?.executeScript) {
    platformName.textContent = 'Browser preview';
    status.textContent = 'For real capture, load Uncanny at chrome://extensions and open it over a playing Short, Reel or TikTok.';
    return;
  }
  try {
    [targetTab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const platform = detectPlatform(targetTab?.url);
    platformName.textContent = platform || 'Unsupported page';
    status.textContent = platform ? 'Play the video. Keep this popup open and stay on the same video while capturing.' : 'Open YouTube Shorts, Instagram or TikTok in this browser.';
    button.disabled = !platform;
  } catch {
    platformName.textContent = 'Page unavailable'; status.textContent = 'Reload the extension, then reopen it on the video.';
  }
}
initialize();
