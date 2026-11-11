#!/usr/bin/env python3
"""Read-only Sheridan / ComfyUI preflight for the Paperspace environment.

This script does not install packages, edit configuration, start services, or
modify model/reference files. Run it from the HerAndHim project directory:

    python scripts/sheridan_preflight.py

Optional environment variables:
    COMFYUI_DIR=/notebooks/ComfyUI
    COMFYUI_URL=http://127.0.0.1:8188
    HERANDHIM_IMAGE_REFERENCE_DIR=/path/to/Image References
    HERANDHIM_IMAGE_PRIMARY_REFERENCE=/path/to/Sheridan_Master.png
"""
from __future__ import annotations

import importlib
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

COMFY_DIR = Path(os.environ.get("COMFYUI_DIR", "/notebooks/ComfyUI")).expanduser()
COMFY_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")
REFERENCE_DIR = Path(os.environ.get("HERANDHIM_IMAGE_REFERENCE_DIR", "")).expanduser()
PRIMARY_REF = Path(os.environ.get("HERANDHIM_IMAGE_PRIMARY_REFERENCE", "")).expanduser()

required_nodes = {
    "InstantIDModelLoader",
    "InstantIDFaceAnalysis",
    "ControlNetLoader",
    "ApplyInstantID",
    "LoadImage",
}
checks: list[tuple[str, str, str]] = []


def report(label: str, status: str, detail: str = "") -> None:
    checks.append((label, status, detail))
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")


def import_check(module: str) -> None:
    try:
        loaded = importlib.import_module(module)
        version = getattr(loaded, "__version__", "version not exposed")
        report(f"Python module: {module}", "OK", str(version))
    except Exception as exc:  # diagnostics must continue after an import failure
        report(f"Python module: {module}", "MISSING", f"{type(exc).__name__}: {exc}")


print("=== Sheridan / Paperspace read-only preflight ===")
print(f"Python: {sys.version.split()[0]} ({sys.executable})")
print(f"ComfyUI directory: {COMFY_DIR}")
print(f"ComfyUI URL: {COMFY_URL}")

for module in ("requests", "PIL", "torch", "insightface", "onnxruntime"):
    import_check(module)

try:
    import torch
    report("CUDA available", "OK" if torch.cuda.is_available() else "WARN",
           torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CUDA not visible to PyTorch")
except Exception as exc:
    report("CUDA available", "MISSING", str(exc))

report("ComfyUI directory", "OK" if COMFY_DIR.is_dir() else "MISSING", str(COMFY_DIR))
if COMFY_DIR.is_dir():
    report("ComfyUI main.py", "OK" if (COMFY_DIR / "main.py").is_file() else "MISSING",
           str(COMFY_DIR / "main.py"))
    custom_nodes = COMFY_DIR / "custom_nodes"
    report("ComfyUI custom_nodes directory", "OK" if custom_nodes.is_dir() else "MISSING",
           str(custom_nodes))

try:
    request = urllib.request.Request(f"{COMFY_URL}/object_info", headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=5) as response:
        import json
        object_info = json.loads(response.read().decode("utf-8"))
    report("ComfyUI API", "OK", f"{len(object_info)} node classes returned")
    missing = sorted(required_nodes - set(object_info))
    report("InstantID node pack", "OK" if not missing else "MISSING",
           "all required node classes found" if not missing else "missing: " + ", ".join(missing))
except (OSError, urllib.error.URLError, ValueError) as exc:
    report("ComfyUI API", "UNAVAILABLE", str(exc))

if REFERENCE_DIR:
    files = sorted(p for p in REFERENCE_DIR.iterdir() if p.is_file()) if REFERENCE_DIR.is_dir() else []
    images = [p for p in files if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
    report("Sheridan reference directory", "OK" if REFERENCE_DIR.is_dir() else "MISSING",
           f"{len(images)} image files" if REFERENCE_DIR.is_dir() else str(REFERENCE_DIR))
else:
    report("Sheridan reference directory", "NOT SET",
           "set HERANDHIM_IMAGE_REFERENCE_DIR to the flat Image References folder")

if PRIMARY_REF:
    report("Sheridan primary face reference", "OK" if PRIMARY_REF.is_file() else "MISSING",
           str(PRIMARY_REF))
else:
    report("Sheridan primary face reference", "NOT SET",
           "set HERANDHIM_IMAGE_PRIMARY_REFERENCE to the approved master portrait")

model_checks = {
    "SDXL checkpoint folder": COMFY_DIR / "models" / "checkpoints",
    "InstantID model folder": COMFY_DIR / "models" / "instantid",
    "InstantID ControlNet folder": COMFY_DIR / "models" / "controlnet",
    "InsightFace model folder": COMFY_DIR / "models" / "insightface" / "models" / "antelopev2",
}
for label, folder in model_checks.items():
    present = folder.is_dir() and any(p.is_file() for p in folder.rglob("*"))
    report(label, "OK" if present else "CHECK", str(folder))

print("\n=== Summary ===")
counts = {status: sum(1 for _, result, _ in checks if result == status)
          for status in ("OK", "WARN", "MISSING", "UNAVAILABLE", "NOT SET", "CHECK")}
print(" | ".join(f"{key}: {value}" for key, value in counts.items() if value))
print("This is a diagnostic only; it does not install or change anything.")
