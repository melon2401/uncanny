# Privacy — Uncanny experimental beta

Uncanny captures video frames only after an analysis action. It uses Chrome's
activeTab and scripting permissions to find the playing video. Direct canvas
capture is preferred. If blocked, visual mode can take a visible-tab screenshot
and crop it to the player; that screenshot can contain other visible page content
in memory before cropping. Motion mode refuses that fallback.

Frames are sent to a Python service on this computer via 127.0.0.1. The extension
has loopback host permission to call that service. No cloud inference, analytics,
or automatic frame storage is implemented. Normal frames/results are in process
memory; clearing/closing the popup discards client state. An already-running local
inference may finish after the popup closes. HTTP logs contain paths/status codes,
not frame bodies. This is not a guarantee of secure erasure from OS memory.

Optional Export sample saves frames, playback timestamps, result, chosen label,
capture date and video URL as JSON in the browser's download location. The user
controls deletion of those files. Do not publish exports without rights/permission.

Setup downloads dependencies from Python package sources and model weights from
the authors' host. Optional DINOv3 setup contacts Hugging Face and uses a local
account token. Tokens are never needed in chat and must not be committed to Git.

This beta does not make an authenticity guarantee. The local HTTP interfaces are
not designed for access from other machines or public hosting.
