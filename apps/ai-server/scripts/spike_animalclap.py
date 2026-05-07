#!/usr/bin/env python
"""W3-v2 Day 1 spike — verify AnimalCLAP audio encoder works.

Downloads risashinoda/animalclap from HF, runs 5-sec silent wav through it,
prints embedding shape + model size.

Architecture notes (from dahlian00/AnimalCLAP source):
  - HFCLAPContrastive wraps laion/clap-htsat-unfused (ClapModel from transformers)
  - ProjectionMLP: 512 -> 512 -> 512
  - Audio input: 48kHz, encode_audio() -> audio_head() -> L2-norm -> [batch, 512]
  - Checkpoint: animalclap_epoch020.pth (raw PyTorch state_dict)
  - Load pattern: torch.load -> strip 'module.' prefix -> load_state_dict(strict=False)

Exit 0 = success, 1 = failure.
"""
from __future__ import annotations

import sys
import time
import traceback

import numpy as np
import torch
import torch.nn as nn

# ---------------------------------------------------------------------------
# Inline model definition (reproduced from dahlian00/AnimalCLAP/train.py)
# so this spike is fully self-contained without cloning the repo.
# ---------------------------------------------------------------------------


class ProjectionMLP(nn.Module):
    def __init__(self, in_dim: int = 512, hidden_dim: int = 512, out_dim: int = 512):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, out_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class HFCLAPContrastive(nn.Module):
    """Minimal replica of AnimalCLAP's contrastive wrapper (audio path only)."""

    def __init__(self, pretrained: str = "laion/clap-htsat-unfused"):
        super().__init__()
        from transformers import ClapModel, ClapProcessor

        print(f"  Loading backbone: {pretrained} ...")
        self.processor = ClapProcessor.from_pretrained(pretrained)
        self.backbone = ClapModel.from_pretrained(pretrained)
        self.audio_head = ProjectionMLP(512, 512, 512)
        self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))

    def encode_audio(self, waveform: torch.Tensor, sample_rate: int = 48000) -> torch.Tensor:
        """waveform: [batch, samples] float32 at sample_rate Hz -> [batch, 512]"""
        inputs = self.processor(
            audio=waveform.cpu().numpy(),
            sampling_rate=sample_rate,
            return_tensors="pt",
        )
        inputs = {k: v.to(next(self.parameters()).device) for k, v in inputs.items()}
        # get_audio_features returns BaseModelOutputWithPooling;
        # .pooler_output holds the projected+normalized audio embedding [batch, proj_dim]
        output = self.backbone.get_audio_features(**inputs)
        return output.pooler_output


# ---------------------------------------------------------------------------
# Main spike logic
# ---------------------------------------------------------------------------


def main() -> int:
    t0 = time.time()
    # GTX 1060 (CC 6.1) is incompatible with this PyTorch build (requires CC>=7.5).
    # Force CPU to avoid CUDA kernel errors during the spike.
    device = "cpu"
    print(f"\n[spike_animalclap] device={device} (forced CPU: GTX1060 CC6.1 not supported by this PyTorch build)")

    # -----------------------------------------------------------------------
    # Step 1: Download checkpoint from HF Hub
    # -----------------------------------------------------------------------
    print("\n[1/5] Downloading animalclap_epoch020.pth from HF Hub ...")
    try:
        from huggingface_hub import hf_hub_download

        ckpt_path = hf_hub_download(
            repo_id="risashinoda/animalclap",
            filename="animalclap_epoch020.pth",
        )
        import os

        ckpt_size_mb = os.path.getsize(ckpt_path) / 1024 / 1024
        print(f"  Checkpoint: {ckpt_path}")
        print(f"  File size:  {ckpt_size_mb:.1f} MB")
    except Exception:
        print("ERROR: Failed to download checkpoint from HF Hub:")
        traceback.print_exc()
        return 1

    # -----------------------------------------------------------------------
    # Step 2: Build model and load checkpoint
    # -----------------------------------------------------------------------
    print("\n[2/5] Building HFCLAPContrastive model ...")
    try:
        model = HFCLAPContrastive("laion/clap-htsat-unfused").to(device)
    except Exception:
        print("ERROR: Failed to build model:")
        traceback.print_exc()
        return 1

    print("\n[3/5] Loading AnimalCLAP checkpoint ...")
    try:
        sd = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        if isinstance(sd, dict) and "state_dict" in sd:
            sd = sd["state_dict"]
        # Strip DDP 'module.' prefix if present
        sd = {k.replace("module.", ""): v for k, v in sd.items()}
        missing, unexpected = model.load_state_dict(sd, strict=False)
        print(f"  Missing keys:    {len(missing)}")
        print(f"  Unexpected keys: {len(unexpected)}")
        if missing:
            print(f"  (first 5 missing): {missing[:5]}")
    except Exception:
        print("ERROR: Failed to load checkpoint:")
        traceback.print_exc()
        return 1

    # -----------------------------------------------------------------------
    # Step 4: Count parameters and report model size
    # -----------------------------------------------------------------------
    print("\n[4/5] Model statistics ...")
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Total parameters:     {total_params:,}")
    print(f"  Trainable parameters: {trainable_params:,}")
    print(f"  Checkpoint file size: {ckpt_size_mb:.1f} MB")

    # -----------------------------------------------------------------------
    # Step 5: Run 5-second silent audio through audio encoder
    # -----------------------------------------------------------------------
    print("\n[5/5] Running 5-sec silent WAV (48kHz) through audio encoder ...")
    try:
        sr = 48000
        duration_sec = 5
        # Silent signal: [1, 48000*5] = [1, 240000]
        waveform = torch.zeros(1, sr * duration_sec, dtype=torch.float32)
        print(f"  Input shape: {list(waveform.shape)} @ {sr}Hz")

        model.eval()
        with torch.no_grad():
            a_feat = model.encode_audio(waveform, sample_rate=sr)
            a_proj = model.audio_head(a_feat)
            a_proj = nn.functional.normalize(a_proj, dim=-1)

        print(f"  encode_audio() output shape: {list(a_feat.shape)}")
        print(f"  audio_head()   output shape: {list(a_proj.shape)}")
        print(f"  Embedding (first 5 values): {a_proj[0, :5].tolist()}")
        print(f"  Embedding L2 norm: {a_proj.norm(dim=-1).item():.6f} (expected ~1.0)")

    except Exception:
        print("ERROR: Failed to run audio encoder:")
        traceback.print_exc()
        return 1

    elapsed = time.time() - t0
    print(f"\n[spike_animalclap] DONE in {elapsed:.1f}s")
    print("=" * 60)
    print("RESULT SUMMARY")
    print("=" * 60)
    print(f"  Checkpoint size:    {ckpt_size_mb:.1f} MB")
    print(f"  Total params:       {total_params:,}")
    print(f"  Embedding shape:    {list(a_proj.shape)}")
    print(f"  Elapsed time:       {elapsed:.1f}s")
    print("  Status:             PASS")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
