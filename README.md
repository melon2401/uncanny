# Uncanny

**Look twice.** A Chrome extension exploring frame-based AI-content detection
for YouTube Shorts, Instagram Reels, and TikTok.

> **Current milestone: local frame scoring.** Uncanny can score six captured stills using the [corrected Community Forensics model](https://huggingface.co/buildborderless/CommunityForensics-DeepfakeDet-ViT/tree/ac6ee457bea904a373065754107451793b56db00). No hashtag or platform label is sent to the scorer.

From the project root, run once (tested with Python 3.12):

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r detector/requirements.txt
```

Start the detector before scoring:

```sh
.venv/bin/python detector/server.py
```

The first start downloads and verifies the model. Leave the terminal open. After capturing frames, click **Score frames on this Mac**. Images are processed in memory on localhost. The display shows the median of six still-image signals on a 0–100 scale. Mixed evidence, or fewer than three distinct center crops, gives an inconclusive result. These prototype thresholds are not calibrated on social videos. The model sees the center of each frame and does not analyze motion or audio.

## Try it locally

1. Download this repository or clone it.
2. Open `chrome://extensions` in Chrome and enable **Developer mode**.
3. Select **Load unpacked**, then choose `apps/extension` inside this repository.
4. Play a Short, Reel, or TikTok and open Uncanny from the extensions menu.
5. Click **Capture frames**. Keep the popup open and stay on that video for
   approximately 6–10 seconds.
6. Scroll down inside the popup to inspect six timestamped thumbnails.

After editing extension files, reload Uncanny on `chrome://extensions`.
Opening `popup.html` as a normal webpage only previews the interface;
capture requires Chrome's extension APIs.

## What works today

- Burnt-orange and cobalt-blue interface with an animated human-to-robot mascot.
- Six sequential frame samples with playback timestamps.
- Direct video-pixel capture where allowed, with a cropped-tab fallback.
- Cancellation, clearing frames, and checks for video or tab changes.
- Local-only processing: a loopback detector, no cloud scoring or tracking.
- Automated tests and a local moving-video fixture.

The user has confirmed seeing captured thumbnails in Chrome. This is an early
prototype, not a guarantee that every player layout on all three platforms works.

## How capture works

The extension selects the largest visible, loaded HTML video. It first draws
decoded video pixels into a canvas. When cross-origin restrictions block that
read, it captures the active tab and crops to the player. Each sample is resized
to a maximum edge of 720 pixels.

The scan animation follows the capture job. Frames stay in popup memory and
disappear when cleared or when the popup closes. Screenshot fallback can include
player controls or text overlaid on the video; burned-in captions also remain.

The planned detector will examine image content, not infer authenticity from
hashtags or platform labels. Six sequential frames cover a short interval, not
an entire video, and say nothing about AI-generated audio.

## Development

Chrome runs the extension without a build step. Tests require Node.js 20 or newer;
there are no npm dependencies to install.

```sh
npm test
npm run check
```

For the standalone video test:

```sh
python3 -m http.server 8766 --bind 127.0.0.1
```

Open `http://127.0.0.1:8766/tests/video-fixture.html` and click the capture button.
This tests actual video-to-canvas sampling using locally generated moving imagery.
The automated suite uses mocked Chrome APIs; it does not replace live site testing.

## Project layout

```text
apps/extension/       Manifest, popup, capture logic and mascot assets
tests/               Automated checks and browser video fixture
docs/                Development roadmap and contribution notes
FRAME-CAPTURE.md      Capture implementation and limitations
```

## What's next

1. Verify direct and fallback capture across all three platforms.
2. Evaluate candidate detection models on known real and synthetic videos.
3. Compare frame scores against source-video ground truth.
4. Calibrate results and allow an inconclusive outcome.

See [the development roadmap](docs/ROADMAP.md). No accuracy claims are made
before evaluation. False positives and false negatives must be measured.

## Design assets

The mascot artwork was generated with AI and iterated using the project's
character brief. The scanning effect is implemented in CSS; it is not a video
analysis model.

## License

[MIT](LICENSE).
