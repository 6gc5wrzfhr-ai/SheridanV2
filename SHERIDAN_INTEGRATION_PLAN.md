# Sheridan + HerAndHim Integration Plan

**Status:** Audit complete; implementation not started  
**Target repository:** `6gc5wrzfhr-ai/SheridanV2`  
**Working branch:** `herandhim-image-integration`  
**Baseline commit:** `08bb1c2740eba1e7cfe25378ea1adca34a9b5568`

## 1. Goal

Deliver one iPhone-first, installable Sheridan PWA backed by the HerAndHim companion engine. Preserve HerAndHim's working chat, memory, scheduling, voice, vision and image-generation capabilities. Bring across the Sheridan-specific identity, visual references, local ComfyUI setup, existing PWA design, and gallery requirements.

This is an integration, not a rewrite. Keep the upstream engine recognisably intact and isolate Sheridan-specific changes behind configuration and small adapters wherever possible.

## 2. Repositories inspected

### HerAndHim foundation — SheridanV2

Inspected the working branch's README, example configuration, FastAPI dashboard, image generator, ComfyUI identity tests, photo album, memory storage, and repository tree.

Confirmed in code:
- FastAPI dashboard and a WebSocket chat endpoint at `/ws/chat`.
- REST routes for access, setup, chat history, tools, config, skills, status, memories, identity/persona/soul, memory index, transcription, and Sanctum photos/status/milestones.
- Access-token middleware gates API and WebSocket access; non-loopback hosting requires authentication.
- Memory uses persistent Markdown records and daily logs; chat history is stored by the session store.
- PhotoAlbum stores generated photos and a canonical reference image on the server.
- Image generation has a ComfyUI backend and saved workflow support. The existing identity workflow aliases include PuLID and InstantID variants; tests check reference upload and workflow placeholder substitution.
- Configuration includes local Ollama, speech-to-text/text-to-speech, selfie scheduling, proactive messaging, and ComfyUI settings.

### Existing Sheridan app — Sheridan_bot

Inspected the current main-branch project brief, PWA shell, app JavaScript, styles, manifest, service worker, Cloudflare Worker, and deployment workflow.

Confirmed in code:
- A dark, iPhone-first PWA shell with standalone display mode and service-worker caching.
- Chat transcript currently stored in localStorage.
- Image and reference uploads are stored in IndexedDB; gallery supports all images, favourites, references, preview and deletion.
- The local WebLLM experiment downloads a small on-device model after user consent. The Worker proxies a fixed model file allowlist and serves static assets.
- The existing app's AI is not yet connected to HerAndHim. If the local model is unavailable, it saves the user's message but does not produce a reply.
- The current PWA does not implement generated-image requests against ComfyUI or the HerAndHim photo album.
- The Sheridan repo also contains character/reference archives and training notebooks. These should remain assets, not be copied wholesale into the runtime app.

## 3. Keep, adapt, replace, build

| Area | Decision | Integration approach |
|---|---|---|
| HerAndHim agent, personality engine, tools | Keep | Use as the single conversation/agent runtime. |
| HerAndHim persistent memory and session store | Keep | Make it the authoritative chat and memory store. |
| Daily life, scheduler, proactive messages, dates | Keep | Configure for Sheridan; verify time zone and delivery channel. |
| Voice and photo understanding | Keep, then test | Use existing STT/TTS and vision providers; expose controls in the PWA after end-to-end tests. |
| HerAndHim ComfyUI image backend | Keep and configure | Point it to the Paperspace ComfyUI endpoint and use a Sheridan identity workflow. |
| HerAndHim PhotoAlbum | Keep as server-side generated-image history | Add metadata/favourites/delete support only if needed; do not duplicate its files in another server store. |
| Sheridan character definition | Adapt | Put the approved Sheridan personality, appearance and boundaries into HerAndHim's persona/soul/profile configuration. |
| Sheridan face/body references | Adapt | Import selected files into the server-side reference store; keep the user's flat `Image References` folder as the source-of-truth archive. |
| Existing Sheridan PWA visual design | Keep/adapt | Port its dark iPhone-first layout, chat, gallery and navigation into the HerAndHim-served PWA. |
| Existing local WebLLM model path | Retire from primary chat, retain only as an optional experiment | Avoid two competing memory/conversation engines. The HerAndHim backend should own chat once connected. |
| Existing localStorage chat transcript | Replace as authoritative history | Read/write through HerAndHim history and WebSocket APIs. Preserve a one-time export/migration path for existing local messages. |
| Existing IndexedDB gallery | Adapt | Keep local-only uploads/references if desired, but clearly distinguish these from generated server-side photos. Add export/backup before any schema changes. |
| Cloudflare Worker | Reassess | Use it for static delivery/reverse proxy only if needed. Do not put model secrets or expose an unauthenticated backend through it. |
| Native iOS wrapper | Defer | First prove the PWA on the actual iPhone; native packaging is a later optional step. |

## 4. Target architecture

1. **iPhone PWA:** Sheridan-branded interface, installable from Safari, with chat, inline images, gallery, memory view and settings.
2. **HerAndHim backend:** single source of truth for the agent, conversation history, memory, schedule, proactive logic, voice and image orchestration.
3. **LLM:** Ollama/local model where the host has sufficient resources, or a provider explicitly selected by the user. Do not silently enable paid APIs.
4. **Image service:** HerAndHim image generator calls the Paperspace ComfyUI workflow. The PWA talks only to the authenticated HerAndHim backend, never directly to an exposed ComfyUI port.
5. **Storage:** HerAndHim's persistent server-side session/memory/photo stores for generated content; optional IndexedDB for device-only uploads/cache. Provide backup/export and avoid accidental duplication.

## 5. Critical integration risks and decisions

- **Hosting and availability:** a PWA is only the interface. If the HerAndHim backend or Paperspace machine is stopped, the related AI/image functions are unavailable. Always-on chat requires an always-on backend/model host; image generation additionally requires an available ComfyUI GPU or another configured image backend.
- **Security:** do not expose the backend or ComfyUI openly. Use HTTPS, strong access tokens, origin restrictions, and authenticated WebSocket connections. Keep provider keys on the server.
- **Cross-origin:** easiest and safest first deployment is to serve the PWA from the same origin as HerAndHim. If Cloudflare hosts the static shell separately, explicitly configure CORS and authenticated API/WebSocket proxying.
- **Data migration:** the old Sheridan PWA's localStorage and IndexedDB data live on the iPhone/browser; HerAndHim data lives on the server. Build an explicit export/import path and test it before changing storage behaviour.
- **Reference semantics:** HerAndHim's current PhotoAlbum canonical-reference method promotes one reference and clears the others. Sheridan has multiple face/body/pose/tattoo references. Do not blindly upload the whole reference set through that single-reference method. Add a multi-reference manifest/selection layer and map selected inputs to the appropriate ComfyUI workflow.
- **ComfyUI workflow compatibility:** validate the actual Paperspace workflow against the installed ComfyUI node versions and the current HerAndHim placeholder contract. The prior IPAdapter schema errors show that workflow JSON must be validated before generation.
- **Licence:** SheridanV2 declares AGPL-3.0-only. If distributing or hosting a modified combined service, review and comply with the licence's source-offer and notice requirements.
- **No feature claims before tests:** README features are not proof of a working deployment. Test each capability end-to-end on the target host and iPhone.

## 6. Phased implementation

### Phase 0 — Baseline and safety
- Keep the original Sheridan_bot repository untouched.
- Keep this integration branch separate from the upstream/default branch.
- Record baseline commit, configuration and tests.
- Back up HerAndHim data and the existing iPhone PWA export before migrations.

### Phase 1 — Backend baseline
- Install/run HerAndHim on the intended host.
- Confirm access-token login, chat WebSocket, history, memory, persona, health/status and restart persistence.
- Run the existing test suite and record failures before modifications.
- Configure Sheridan persona and local LLM without paid API credentials.

### Phase 2 — Sheridan PWA shell
- Port the existing Sheridan visual shell into the HerAndHim-served static UI.
- Replace local-only chat submission with authenticated `/ws/chat` and history retrieval.
- Preserve mobile layout, gallery navigation, local upload and reference-management screens.
- Verify reconnect, token expiry, offline shell behaviour and iPhone standalone mode.

### Phase 3 — Identity and ComfyUI
- Add a managed multi-reference set: face identity, body/physique, pose, tattoos and style, with a selected primary face anchor.
- Keep original reference files in the user's flat `Image References` folder.
- Configure the Paperspace ComfyUI endpoint privately and add a server-side workflow adapter.
- Validate workflow inputs, upload/reference handling, output retrieval, failure reporting and GPU-offline behaviour.

### Phase 4 — Generated image gallery
- Display generated photos inline in chat and in a dated gallery.
- Add favourite/delete controls and metadata.
- Keep uploaded reference images separate from generated photos.
- Add export/backup and retention controls before enabling automatic cleanup.

### Phase 5 — Additional capabilities
- Expose memory timeline/search, daily schedule and settings.
- Test voice input/output and photo understanding.
- Test proactive messages and selfie scheduling only after delivery channel and host uptime are reliable.

### Phase 6 — Acceptance and release
- Run regression tests for existing HerAndHim features.
- Test on iPhone Safari and Home Screen installation.
- Verify restart persistence, data export, access controls, HTTPS, and no unexpected paid API calls.
- Only then consider replacing the older app link or creating a native wrapper.

## 7. Acceptance checklist

- [ ] Existing HerAndHim chat and history still work.
- [ ] Existing memory survives restart and remains searchable.
- [ ] Sheridan persona and identity load consistently.
- [ ] PWA installs and behaves correctly on iPhone.
- [ ] Chat works through the backend; no duplicate local conversation engine.
- [ ] ComfyUI generation uses the selected Sheridan references and saves results.
- [ ] Generated images appear inline and in the dated gallery.
- [ ] Uploaded references remain distinct from generated images.
- [ ] Voice, vision, scheduler and proactive features pass explicit tests.
- [ ] Backend and ComfyUI are not publicly exposed without authentication.
- [ ] Existing local PWA data can be exported/migrated.
- [ ] No paid provider is activated without explicit user approval.

## 8. Current status

**Audit complete. No application code, deployment settings, user data, or existing working app has been changed by this audit.** The integration branch is still at its recorded baseline commit. The next implementation task should be Phase 1: establish and test the HerAndHim backend on the chosen host before porting the Sheridan interface.
