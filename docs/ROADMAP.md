# Development roadmap

## Completed: interface and capture

- [x] Chrome Manifest V3 extension
- [x] Orange/blue theme and scanning mascot
- [x] Six-frame sampling and timestamped thumbnails
- [x] Direct-pixel capture and screenshot-crop fallback
- [x] Cancel/clear controls and playback checks
- [x] Eight automated tests and moving-video browser fixture
- [x] User-confirmed thumbnail capture in Chrome

## Next: capture validation

- [ ] Record Chrome version, platform and capture method for each manual test.
- [ ] Test Shorts, Reels and TikTok feed transitions and paused playback.
- [ ] Check overlays, partially visible players and different zoom levels.
- [ ] Improve error reporting for restricted or protected players.

## Then: detector evaluation

- [ ] Compare model licenses, deployment requirements and inference costs.
- [ ] Build a small, permissioned real/synthetic evaluation set.
- [ ] Separate examples by source video to prevent train/test leakage.
- [ ] Evaluate compression, animation, filters and unseen generators.
- [ ] Report false-positive and false-negative rates, not just accuracy.
- [ ] Decide when insufficient evidence should produce an inconclusive result.

## Then: backend and integration

- [ ] Define a versioned frame-analysis API.
- [ ] Add request limits, validation, timeouts and cancellation behavior.
- [ ] Obtain explicit consent before transmitting captured frames.
- [ ] Keep provider credentials on the server, never in the extension.
- [ ] Wire real results into the interface without treating scores as proof.

## Later

- [ ] Broader temporal/video analysis and separate audio analysis.
- [ ] Mobile share-to-analyze workflow.
- [ ] Chrome Web Store packaging and privacy documentation.

No dates or completed milestones are fabricated. Commit dates record when work
is saved to this repository; initial commits organize work developed before publication.
