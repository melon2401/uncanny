"""Shared frozen DINOv3 feature transform for training and local inference."""
import io
import hashlib
import sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FEATURE_VERSION = "dinov3-l16-full-frame-224-bilinear-mean-l2-v1"
BACKBONE_SHA256 = "dcb2e45127cccbf1601e5f42fef165eea275c8e5213197e8dcf3f48822718179"


def capture_image(image):
    """Match extension JPEG capture: long edge <=1280, quality 90, no upscale."""
    image = image.convert("RGB")
    if max(image.size) > 1280:
        scale = 1280 / max(image.size)
        image = image.resize(tuple(max(1, round(s * scale)) for s in image.size), Image.Resampling.BILINEAR)
    data = io.BytesIO()
    image.save(data, format="JPEG", quality=90)
    captured = Image.open(io.BytesIO(data.getvalue())).convert("RGB")
    captured.info["capture_jpeg"] = data.getvalue()
    return captured


def compressed_image(image):
    """Predeclared extra training view; applied equally to both classes."""
    scale = min(1, 256 / min(image.size))
    image = image.resize(tuple(max(1, round(s * scale)) for s in image.size), Image.Resampling.BILINEAR)
    data = io.BytesIO()
    image.save(data, format="JPEG", quality=50)
    return Image.open(io.BytesIO(data.getvalue())).convert("RGB")


def clip_feature(frames):
    x = np.asarray(frames, dtype=np.float32)
    if x.ndim != 2 or x.shape[0] != 6 or not np.isfinite(x).all():
        raise ValueError("Expected six finite frame embeddings")
    x = x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)
    feature = x.mean(axis=0)
    return feature / max(float(np.linalg.norm(feature)), 1e-12)


class Embedder:
    def __init__(self, device="mps"):
        import torch
        from transformers import AutoModel
        if device == "mps" and not torch.backends.mps.is_available():
            raise ValueError("MPS unavailable; run with GPU access or select cpu")
        with (ROOT / ".models/dinov3-hf/model.safetensors").open("rb") as weights:
            if hashlib.file_digest(weights,"sha256").hexdigest() != BACKBONE_SHA256:
                raise ValueError("DINOv3 weights differ from the pinned official checkpoint")
        self.device = device
        self.model = AutoModel.from_pretrained(ROOT / ".models/dinov3-hf", local_files_only=True).eval().to(device)
        config = self.model.config
        if (config.model_type, config.hidden_size, config.num_hidden_layers, config.patch_size) != ("dinov3_vit",1024,24,16):
            raise ValueError("Expected the approved DINOv3 ViT-L model")

    def __call__(self, images):
        import torch
        pixels = np.stack([np.asarray(im.resize((224, 224), Image.Resampling.BILINEAR), dtype=np.float32)
                           .transpose(2, 0, 1) / 255.0 for im in images])
        pixels = (pixels - np.array([.485, .456, .406], dtype=np.float32)[None, :, None, None]) / np.array(
            [.229, .224, .225], dtype=np.float32)[None, :, None, None]
        features = []
        with torch.inference_mode():
            for i in range(0, len(images), 3):
                output = self.model(pixel_values=torch.from_numpy(pixels[i:i+3]).to(self.device)).pooler_output
                features.append(output.cpu().numpy())
        return np.concatenate(features)


def video_frames(path):
    sys.path.insert(0, str(ROOT / ".models/training-deps"))
    import av
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        duration = float(stream.duration * stream.time_base) if stream.duration else container.duration / 1_000_000
        if not np.isfinite(duration) or duration <= 0:
            raise ValueError("Invalid video duration")
        images, timestamps = [], []
        for target in np.linspace(duration * .1, duration * .9, 6):
            container.seek(int(target / stream.time_base), stream=stream, backward=True)
            chosen = None
            for frame in container.decode(stream):
                chosen = frame
                if frame.time is not None and frame.time >= target:
                    break
            if chosen is None or chosen.time is None:
                raise ValueError(f"Could not decode requested frame in {path}")
            images.append(capture_image(chosen.to_image()))
            timestamps.append(chosen.time)
    if len(set(timestamps)) < 3:
        raise ValueError("Fewer than three distinct decoded timestamps")
    return images, timestamps
