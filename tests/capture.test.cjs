const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '../apps/extension');
const source = fs.readFileSync(path.join(root, 'capture.js'), 'utf8');
const url = 'https://www.youtube.com/shorts/example';

function fixture(blockPixels = false) {
  const video = { readyState: 4, videoWidth: 360, videoHeight: 640, currentTime: 1,
    currentSrc: 'blob:video-one', paused: false, ended: false,
    getBoundingClientRect: () => ({ left: 100, top: 20, right: 460, bottom: 660, width: 360, height: 640 }) };
  const style = { visibility: 'visible', display: 'block', opacity: '1', objectPosition: '50% 50%', transform: 'none', objectFit: 'contain' };
  const context = vm.createContext({ URL, location: { href: url }, innerWidth: 1000, innerHeight: 800,
    getComputedStyle: () => style,
    document: { querySelectorAll: () => [video], createElement: () => ({ getContext: () => ({ drawImage() {} }), toDataURL() {
      if (blockPixels) { const e = new Error('CORS'); e.name = 'SecurityError'; throw e; }
      return 'data:image/jpeg;base64,frame';
    } }) } });
  vm.runInContext(source, context);
  return { context, video, style, sample: () => context.sampleVideo('job', url) };
}
test('accepts real platform hosts, rejects lookalike hosts and ordinary YouTube pages', () => {
  const { context: c } = fixture();
  for (const u of ['https://www.youtube.com/shorts/x', 'https://www.instagram.com/reels/', 'https://www.tiktok.com/@a/video/1']) assert.ok(c.detectPlatform(u));
  for (const u of ['https://youtube.com.evil.test/shorts/x', 'https://example.com/?tiktok.com', 'https://www.youtube.com/watch?v=x']) assert.equal(c.detectPlatform(u), null);
});
test('samples clean pixels and refuses paused or stalled playback', () => {
  const f = fixture(); assert.equal(f.sample().method, 'Video pixels');
  assert.throws(f.sample, /stalled/);
  f.video.currentTime = 2; f.video.paused = true; assert.throws(f.sample, /paused/);
});
test('does not mix a changed video or navigation into the same session', () => {
  const f = fixture(); f.sample(); f.video.currentSrc = 'blob:other';
  assert.throws(f.sample, /video changed/);
  f.context.location.href = 'https://example.com'; assert.throws(f.sample, /page changed/);
});
test('CORS fallback calculates a centered letterbox crop and retina coordinates', () => {
  const f = fixture(true); f.video.videoWidth = 640; f.video.videoHeight = 360;
  const frame = f.sample(); assert.equal(frame.method, 'Visible video crop');
  assert.equal(frame.rect.width, 360); assert.equal(frame.rect.height, 202.5);
  const r = f.context.cropBounds(frame, 2000, 1600);
  assert.equal(r.x, 200); assert.equal(r.y, 478); assert.equal(r.width, 720); assert.equal(r.height, 405);
});
test('refuses hidden, partial, and unsupported transformed players', () => {
  const f = fixture(true); f.style.display = 'none'; assert.throws(f.sample, /No visible/);
  f.style.display = 'block'; f.style.transform = 'matrix(1,0,0,1,0,0)'; assert.throws(f.sample, /layout/);
  f.video.currentTime++; f.style.transform = 'none'; f.context.innerHeight = 300; assert.throws(f.sample, /entire video/);
});

function popupHarness({ cancel = false, switchTab = false } = {}) {
  const els = new Map();
  const element = () => ({ children: [], textContent: '', hidden: true, disabled: false,
    classList: { add() {}, remove() {} }, listeners: {},
    addEventListener(name, cb) { this.listeners[name] = cb; },
    replaceChildren() { this.children = []; }, append(...children) { this.children.push(...children); } });
  const doc = { getElementById(id) { if (!els.has(id)) els.set(id, element()); return els.get(id); }, createElement: element };
  let samples = 0;
  const tab = { id: 7, windowId: 1, url };
  const ctx = vm.createContext({ console, URL, crypto: { randomUUID: () => 'job' }, document: doc, window: { addEventListener() {} },
    AbortController, clearTimeout() {}, fetch: async () => ({ok:true,json:async () => ({signal:5,label:'Inconclusive',frames:[1,2,3,7,8,9]})}),
    setTimeout: (resolve, ms) => { if (ms === 45000) return 1; if (cancel) els.get('analyze-button').listeners.click(); resolve(); },
    chrome: { tabs: { query: async () => [{ ...tab, id: switchTab && samples ? 8 : 7 }] }, scripting: { executeScript: async () => [{ result: { time: ++samples, data: 'data:image/jpeg;base64,frame', method: 'Video pixels' } }] } } });
  vm.runInContext(source, ctx);
  vm.runInContext(fs.readFileSync(path.join(root, 'score.js'), 'utf8'), ctx);
  vm.runInContext(fs.readFileSync(path.join(root, 'popup.js'), 'utf8'), ctx);
  return { ctx, els, samples: () => samples };
}
test('capture flow renders exactly six timestamped frames and clear removes them', async () => {
  const h = popupHarness(); await h.ctx.initialize(); await h.ctx.capture();
  assert.equal(h.samples(), 6); assert.equal(h.els.get('frames').children.length, 6);
  assert.equal(h.els.get('headline').textContent, 'Analysis complete.');
  h.els.get('clear-frames').listeners.click(); assert.equal(h.els.get('frames').children.length, 0);
});
test('cancellation discards partial frames and restores controls', async () => {
  const h = popupHarness({ cancel: true }); await h.ctx.initialize(); await h.ctx.capture();
  assert.equal(h.samples(), 1); assert.equal(h.els.get('frames').children.length, 0);
  assert.equal(h.els.get('headline').textContent, 'Capture cancelled.');
  assert.equal(h.els.get('analyze-button').disabled, false);
});
test('tab switch aborts before sampling another frame', async () => {
  const h = popupHarness({ switchTab: true }); await h.ctx.initialize(); await h.ctx.capture();
  assert.equal(h.samples(), 1); assert.equal(h.els.get('frames').children.length, 0);
  assert.match(h.els.get('status').textContent, /active page changed/);
});
test('local score uses captured pixels and lets the user retry after an offline error', async () => {
  const h = popupHarness(); await h.ctx.initialize(); await h.ctx.capture();
  Object.assign(h.ctx, {AbortController, TypeError, setTimeout: () => 1, clearTimeout() {}});
  const click = h.els.get('score-frames').listeners.click;
  h.ctx.fetch = async () => { throw new TypeError('offline'); };
  await click();
  assert.match(h.els.get('score-result').textContent, /Local detector unavailable/);
  assert.equal(h.els.get('score-frames').disabled, false);
  h.ctx.fetch = async (url, options) => {
    assert.equal(url, 'http://127.0.0.1:8767/v1/score');
    assert.equal(JSON.parse(options.body).frames.length, 6);
    return {ok:true, json:async () => ({signal:51,label:'Inconclusive',frames:[1,1,50,52,99,99]})};
  };
  await click(); assert.match(h.els.get('score-result').textContent, /Inconclusive · 51\/100/);
});
