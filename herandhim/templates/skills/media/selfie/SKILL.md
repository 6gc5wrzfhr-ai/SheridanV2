---
name: selfie
description: "Generate and send a selfie of yourself (the AI companion) to the user using the configured image provider, including local ComfyUI. Use when the user asks for a photo or when a spontaneous photo would naturally enrich the conversation. NOT for: generic image generation (use image_gen), photo editing, or screenshots."
dependencies: requests
metadata:
  emoji: "🤳"
---

# Selfie (AI Partner Self-Portrait)

Take an in-character self-portrait reflecting your current scene (from today's
planner) and your appearance.  The photo is sent via the active channel.

## When to Use

✅ **USE this skill when:**

- "发张自拍" / "拍张照片给我看看"
- "你现在在干嘛，让我看看"
- "今天穿了什么？"
- Spontaneously sharing a moment ("我现在在阳台喝咖啡，看")

## When NOT to Use

❌ **DON'T use this skill when:**

- The user asks for a generic image / illustration → use `image_gen`
- They want a photo of something other than yourself → use `image_gen`
- They want to edit an existing image
- Selfie feature is disabled (`selfie.enabled = false` in config) or no usable image provider is configured

## Setup

Uses the image provider selected in `skills.image.provider`. For local generation, set it to `comfyui` and configure the ComfyUI URL and identity workflow:

```json
"skills": {
  "image": {
    "provider": "comfyui",
    "referenceDirectory": "/path/to/Image References",
    "primaryReference": "/path/to/Image References/Sheridan_Master.png"
  },
  "comfyui": {
    "baseUrl": "http://127.0.0.1:8188",
    "identityWorkflow": "sdxl-instantid",
    "checkpoint": "your-sdxl-checkpoint.safetensors"
  }
}
```

You can use `HERANDHIM_IMAGE_REFERENCE_DIR` and
`HERANDHIM_IMAGE_PRIMARY_REFERENCE` instead of the two reference paths.
The reference directory is read-only: HerAndHim does not rename or delete your
source images. The explicitly selected primary reference is used as the face
anchor. The rest of the source collection is preserved unchanged for the next
stage, when we add separate body, pose, expression and tattoo conditioning.

## Commands

### Take a selfie reflecting the current scene

```bash
python {skill_path}/take_selfie.py
```

### With a scene hint

```bash
python {skill_path}/take_selfie.py --hint "刚画完水彩，举起来给镜头看"
```

### Override model

```bash
python {skill_path}/take_selfie.py --model seedream-5-0-260128
```

## Notes

- Generation speed depends on the selected backend and available GPU
- Photos auto-save to `~/.herandhim/context/photos/` and are pruned after 30 days
- The primary face reference is passed to identity-capable backends; ComfyUI uses the configured InstantID/PuLID workflow
- Seed is deterministic from the character description, so consistency improves
  even without a reference photo

## Resources

| File | Description |
|------|-------------|
| `take_selfie.py` | Calls `take_selfie()` and sends the result via the active channel |
