"""
Training script for a small ESPCN (Efficient Sub-Pixel Convolutional
Network) super-resolution model, run once locally to produce an ONNX
file the backend loads for inference.

Why ESPCN: it's a well-known, genuinely lightweight SR architecture
(Shi et al., 2016) - a handful of conv layers plus a pixel-shuffle
upsampling layer. Small enough (~50-100KB of weights) to run comfortably
on a free-tier server with no GPU, unlike research-grade models like
SEN2SR or SwinIR which need far more memory/compute than a 512MB Render
instance has.

HONESTY NOTE: this is trained via self-supervised degradation (downscale
a real Sentinel-2 scene, train the model to reverse it) using ONE real
scene's patches with augmentation - not a large curated dataset. It will
genuinely learn to sharpen edges/textures better than plain
interpolation, but it is not comparable to a properly trained,
validated research model. Label it accordingly everywhere.
"""
import numpy as np
import rasterio
import torch
import torch.nn as nn
import torch.nn.functional as F


class ESPCN(nn.Module):
    """
    Residual formulation: the network predicts a CORRECTION on top of a
    plain bicubic upsample, rather than reconstructing the whole image
    from scratch. This is a standard, well-established trick for small
    SR models - it dramatically improves quality/stability with limited
    training data, and specifically reduces checkerboard artifacts from
    the pixel-shuffle layer, since the network only needs to learn fine
    detail rather than full image reconstruction.
    """
    def __init__(self, n_bands: int = 4, scale_factor: int = 4):
        super().__init__()
        self.scale_factor = scale_factor
        self.body = nn.Sequential(
            nn.Conv2d(n_bands, 64, kernel_size=5, padding=2),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
        )
        self.upsample = nn.Conv2d(32, n_bands * (scale_factor ** 2), kernel_size=3, padding=1)
        self.pixel_shuffle = nn.PixelShuffle(scale_factor)
        # zero-init the last layer so the model starts as a no-op correction
        # (pure bicubic) and learns to deviate from there - much more stable
        nn.init.zeros_(self.upsample.weight)
        nn.init.zeros_(self.upsample.bias)

    def forward(self, x):
        bicubic = F.interpolate(x, scale_factor=self.scale_factor, mode="bicubic", align_corners=False)
        correction = self.body(x)
        correction = self.upsample(correction)
        correction = self.pixel_shuffle(correction)
        return torch.clamp(bicubic + correction, 0, 1)


def load_training_bands(path: str) -> np.ndarray:
    """Read all bands, normalize to 0-1 reflectance-ish range."""
    with rasterio.open(path) as ds:
        arr = ds.read().astype(np.float32)
    arr = arr / 10000.0
    return np.clip(arr, 0, 1)


def make_patch_pairs(bands: np.ndarray, patch_size: int, scale: int, n_patches: int):
    """
    Self-supervised pair generation: crop an HR patch from the real scene,
    downsample it to make the LR input, train the model to reverse that.
    Includes flip/rotation augmentation since we only have one real scene.
    """
    n_bands, h, w = bands.shape
    pairs = []
    rng = np.random.default_rng(42)

    for _ in range(n_patches):
        if h <= patch_size or w <= patch_size:
            hr = bands
        else:
            y = rng.integers(0, h - patch_size)
            x = rng.integers(0, w - patch_size)
            hr = bands[:, y:y + patch_size, x:x + patch_size]

        # augmentation: random flip/rotation for more effective training diversity
        if rng.random() < 0.5:
            hr = hr[:, :, ::-1].copy()
        if rng.random() < 0.5:
            hr = hr[:, ::-1, :].copy()
        k = rng.integers(0, 4)
        hr = np.rot90(hr, k=k, axes=(1, 2)).copy()

        hr_t = torch.from_numpy(hr).unsqueeze(0)
        lr_t = F.interpolate(hr_t, scale_factor=1 / scale, mode="bilinear", align_corners=False)
        lr_t = F.interpolate(lr_t, size=hr_t.shape[-2:], mode="nearest")  # placeholder, replaced below
        pairs.append((hr_t.squeeze(0)))

    return pairs


def gradient_loss(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """
    Penalizes missing edges/sharpness, not just raw pixel error. Plain
    MSE alone is well known to produce blurry super-resolution results
    since it rewards "safe" smooth averages; adding a gradient term
    pushes the model to actually reproduce edges.
    """
    def grad(x):
        dx = x[:, :, :, 1:] - x[:, :, :, :-1]
        dy = x[:, :, 1:, :] - x[:, :, :-1, :]
        return dx, dy

    pred_dx, pred_dy = grad(pred)
    target_dx, target_dy = grad(target)
    return F.l1_loss(pred_dx, target_dx) + F.l1_loss(pred_dy, target_dy)


def train():
    print("Loading real Sentinel-2 data for training...")
    bands = load_training_bands("../data/input/real_sentinel2_stacked.tif")
    print("bands shape:", bands.shape)

    scale = 4
    patch_size = 64
    n_bands = bands.shape[0]

    model = ESPCN(n_bands=n_bands, scale_factor=scale)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=3000)

    rng = np.random.default_rng(42)
    _, h, w = bands.shape

    n_steps = 3000
    batch_size = 12
    losses = []

    for step in range(n_steps):
        hr_batch = []
        for _ in range(batch_size):
            if h <= patch_size or w <= patch_size:
                hr = bands
                pad_h = max(0, patch_size - hr.shape[1])
                pad_w = max(0, patch_size - hr.shape[2])
                if pad_h or pad_w:
                    hr = np.pad(hr, ((0, 0), (0, pad_h), (0, pad_w)), mode="reflect")
                hr = hr[:, :patch_size, :patch_size]
            else:
                y = rng.integers(0, h - patch_size)
                x = rng.integers(0, w - patch_size)
                hr = bands[:, y:y + patch_size, x:x + patch_size]

            if rng.random() < 0.5:
                hr = hr[:, :, ::-1].copy()
            if rng.random() < 0.5:
                hr = hr[:, ::-1, :].copy()
            k = int(rng.integers(0, 4))
            hr = np.ascontiguousarray(np.rot90(hr, k=k, axes=(1, 2)))

            hr_batch.append(hr)

        hr_t = torch.from_numpy(np.stack(hr_batch)).float()
        lr_t = F.interpolate(hr_t, scale_factor=1 / scale, mode="bicubic", align_corners=False)
        lr_t = torch.clamp(lr_t, 0, 1)

        pred = model(lr_t)
        mse = F.mse_loss(pred, hr_t)
        grad_l = gradient_loss(pred, hr_t)
        loss = mse + 0.5 * grad_l

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        scheduler.step()

        losses.append(loss.item())
        if step % 300 == 0 or step == n_steps - 1:
            print(f"step {step}: loss={loss.item():.5f} (mse={mse.item():.5f}, grad={grad_l.item():.5f})")

    print("Final loss:", losses[-1])
    print("Loss reduction:", losses[0], "->", losses[-1])

    torch.save(model.state_dict(), "/tmp/espcn_weights.pt")
    return model, scale, n_bands


if __name__ == "__main__":
    train()
