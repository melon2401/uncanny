// Each call samples one frame in an isolated extension world, not the site's scripts.
function sampleVideo(session, expectedUrl) {
  if (location.href !== expectedUrl) throw new Error('The page changed. Reopen Uncanny on the video you want.');
  const candidates = [...document.querySelectorAll('video')].map(video => {
    const r = video.getBoundingClientRect(), style = getComputedStyle(video);
    const left = Math.max(0, r.left), top = Math.max(0, r.top);
    const right = Math.min(innerWidth, r.right), bottom = Math.min(innerHeight, r.bottom);
    const area = Math.max(0, right - left) * Math.max(0, bottom - top);
    const visible = style.visibility !== 'hidden' && style.display !== 'none' && Number(style.opacity) > 0;
    return { video, r, area: visible ? area : 0 };
  }).filter(x => x.area > 10000 && x.video.readyState >= 2 && x.video.videoWidth > 0)
    .sort((a, b) => b.area - a.area);
  if (!candidates.length) throw new Error('No visible, loaded video found. Open a video and press play.');
  const { video, r } = candidates[0];
  const source = video.currentSrc, old = globalThis.__uncannyFrameSession;
  if (old?.session === session && (old.video !== video || old.source !== source)) throw new Error('The video changed. Stay on one video and try again.');
  if (video.paused || video.ended) throw new Error('The video is paused. Press play, then capture again.');
  if (old?.session === session && Math.abs(video.currentTime - old.time) < 0.08) throw new Error('Playback has stalled. Let the video load, then try again.');
  globalThis.__uncannyFrameSession = { session, video, source, time: video.currentTime };
  const frame = { time: video.currentTime, source, page: location.href, viewport: { width: innerWidth, height: innerHeight }, element: { left: r.left, top: r.top, width: r.width, height: r.height } };
  // Prefer clean video pixels, without page captions and controls.
  const canvas = document.createElement('canvas');
  const scale = Math.min(1, 720 / Math.max(video.videoWidth, video.videoHeight));
  canvas.width = Math.round(video.videoWidth * scale); canvas.height = Math.round(video.videoHeight * scale);
  try {
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    frame.data = canvas.toDataURL('image/jpeg', 0.9);
    frame.method = 'Video pixels';
    return frame;
  } catch (error) { if (error.name !== 'SecurityError') throw error; }
  // Cross-origin players can block pixel reads: return crop coordinates instead.
  const style = getComputedStyle(video);
  if (style.objectPosition !== '50% 50%' || style.transform !== 'none') throw new Error('This player layout cannot be cropped reliably yet.');
  let left = r.left, top = r.top, width = r.width, height = r.height;
  if (style.objectFit === 'contain' || style.objectFit === 'scale-down') {
    let s = Math.min(width / video.videoWidth, height / video.videoHeight);
    if (style.objectFit === 'scale-down') s = Math.min(1, s);
    const w = video.videoWidth * s, h = video.videoHeight * s;
    left += (width - w) / 2; top += (height - h) / 2; width = w; height = h;
  } else if (!['cover', 'fill'].includes(style.objectFit)) throw new Error('This player layout cannot be cropped reliably yet.');
  if (left < -1 || top < -1 || left + width > innerWidth + 1 || top + height > innerHeight + 1) throw new Error('Keep the entire video visible before capturing.');
  frame.rect = { left: Math.max(0, left), top: Math.max(0, top), width, height };
  frame.method = 'Visible video crop';
  return frame;
}

function detectPlatform(raw) {
  try {
    const url = new URL(raw), host = url.hostname.replace(/^www\./, '');
    if (host === 'youtube.com' && url.pathname.startsWith('/shorts/')) return 'YouTube Short';
    if (host === 'instagram.com') return 'Instagram';
    if (host === 'tiktok.com') return 'TikTok';
  } catch { /* Invalid URL is unsupported. */ }
  return null;
}

function cropBounds(frame, imageWidth, imageHeight) {
  const sx = imageWidth / frame.viewport.width, sy = imageHeight / frame.viewport.height;
  const x = Math.max(0, Math.round(frame.rect.left * sx)), y = Math.max(0, Math.round(frame.rect.top * sy));
  const width = Math.min(imageWidth - x, Math.round(frame.rect.width * sx));
  const height = Math.min(imageHeight - y, Math.round(frame.rect.height * sy));
  if (width <= 0 || height <= 0) throw new Error('The video is outside the visible area.');
  return { x, y, width, height };
}
