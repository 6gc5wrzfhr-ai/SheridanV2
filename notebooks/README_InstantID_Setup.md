# Sheridan InstantID setup package

This package adds a guided, no-LoRA setup for the existing HerAndHim ComfyUI identity workflow.

## What it does

- Uses the existing ComfyUI folder at `/notebooks/ComfyUI`.
- Installs the native `cubiq/ComfyUI_InstantID` node pack and InsightFace dependencies.
- Downloads the InstantID adapter, InstantID ControlNet, InsightFace antelopev2 models, and the SDXL-derived SSD-1B checkpoint.
- Checks required files and prints the HerAndHim image settings.

## Run it in Paperspace

1. Update the existing `SheridanV2` repository to this branch, or download `notebooks/Sheridan_InstantID_Setup.ipynb` from this branch and upload it into JupyterLab.
2. Open the notebook and run the first **Preflight** cell.
3. Check that it finds `/notebooks/ComfyUI/main.py`, CUDA, and at least 10 GB free disk.
4. Run the remaining cells in order. The model download step is about 9 GB. It skips files that are already present.
5. Restart ComfyUI after the notebook completes.

Do not run the download cell if preflight reports less than 10 GB free. Do not delete or overwrite existing model files.

## HerAndHim settings (after ComfyUI is verified)

- `skills.comfyui.checkpoint`: `SSD-1B.safetensors`
- `skills.comfyui.identityWorkflow`: `sdxl-instantid`

The ComfyUI API address and Docker-to-host networking must be verified separately before enabling generation from the iPhone. This package intentionally does not change the HerAndHim Docker networking or live configuration.

## Important limits

- This is a setup notebook, not a claim that image generation is already running.
- InstantID is SDXL-only. SSD-1B is an SDXL-derived 1B-parameter checkpoint and is smaller than standard SDXL, but an 8 GB GPU may still need ComfyUI low-VRAM settings and modest image dimensions.
- The workflow uses one face reference per generation. Pose is influenced by the reference/keypoints; changing poses may require a separate pose/keypoint image.
- No LoRA training is performed.
