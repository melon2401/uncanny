# Portrait capture quality investigation

The visual pipeline capped the longest edge at 720, so 1080x1920 portrait video
became 405x720. WaveRep's original 504-square CenterCrop then added black padding.
This is a capture/preprocessing interaction, not proof of the cause of every error.

Diagnostic on 22 already-inspected exports: bicubic enlargement to minimum side 504
before cropping changed a real inconclusive sample to negative evidence, but also
changed a previously AI-positive sample to inconclusive. Another AI-negative sample
became inconclusive. Other display outcomes remained unchanged. No decision
thresholds were changed. This resize variant was NOT promoted.

Instead, new visual captures retain up to 1280 pixels on the longest edge, without
upscaling. A 1080x1920 source therefore yields 720x1280, enough for the model's
original crop without padding. Motion remains capped at 720 to retain its existing
calibration/input path. The visual server accepts 1280-edge frames and reports input
dimensions and the number requiring padding. The UI surfaces low source resolution.

Tests cover preserved dimensions, unchanged motion limits and no source upscaling.
Old exports cannot recover lost detail. No higher-resolution detection accuracy
claim is established; fresh captures are needed to measure that effect. Source
quality, cropping, model generalization and screenshot overlays remain limitations.
The newest saved export during this investigation was from November 12; the user's
latest reported November 16 failure was not available as a saved sample.

Diagnostic: detector/inspect_padding.py, using local cached results and captures.
Private per-frame findings are in ignored captures/padding-ablation.json.
