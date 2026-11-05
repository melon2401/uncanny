# Frame capture milestone

Load `apps/extension` as an unpacked Chrome extension, or reload the existing
Uncanny card at `chrome://extensions`. Version 0.2.0 adds the `scripting`
permission alongside `activeTab`. No permanent site access is requested.

Play a YouTube Short, Instagram Reel or TikTok. Open Uncanny from the Chrome
toolbar, click **Capture frames**, and leave the popup open on the same video.
Six frames appear below the button after approximately six to ten seconds.
Scroll inside the popup to inspect the thumbnails and their playback timestamps.

`capture.js` finds the largest visible loaded HTML video, checks playback, and
first attempts a canvas read of the decoded video pixels (maximum edge 720px).
If cross-origin restrictions prevent this, `popup.js` captures the active tab
and immediately crops to the visible video. That fallback may include player
overlays or burned-in captions; it does not claim to remove those.

Frames remain in popup memory, are never uploaded, and disappear when the popup
closes or Clear frames is pressed. Cancel discards partial captures. Changing
the tab, URL, video element/source, or pausing/stalling playback aborts a run.
The animation follows the actual capture job, not a simulated AI percentage.

## Checks

Run `node --test tests/capture.test.cjs` from this folder. Tests cover platform
validation, source changes, paused/stalled playback, crop scaling/letterboxing,
cancellation, tab switching and six-frame rendering using mocked Chrome APIs.

Serve this folder locally and open `tests/video-fixture.html` to exercise real
browser video-to-canvas sampling against a locally generated moving video.

## Limits

This is frame capture, not AI detection. Live social-platform integration needs
testing in Chrome: protected media, nested frames, overlays, transformed players,
or site changes may need additional handling. Six sequential frames sample a
short interval, not the entire clip. Browser/file previews cannot access Chrome
extension APIs and intentionally disable capture.
