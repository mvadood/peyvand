# Peyvand — reading-room backgrounds

The user chose to proceed with the natural reading-room direction and requested one background each for Milad and Hooman, leaving sizing, placement and the remaining implementation to Claude. These are clean background plates, with no people, captions, logo or framing baked in.

## Files

- `milad-reading-room-v1.png`: window and left walnut shelves; softly lit plaster toward the centre/right.
- `hooman-reading-room-v1.png`: plaster toward the centre/left, right walnut bookcase and deeper lamp-lit alcove.
- `reading-room-v1.png`: original wide concept, useful for visual reference.
- `speaker-background-prompts.json`: full prompts and generation provenance (built-in image generation).
- `speaker-background-manifest.json`: actual source dimensions and checksums.

Both views were generated from the same room reference and visually checked for matching materials and daylight direction. They are coordinated generated views, not calibrated photographs or a 3D scene. Keep the original files; crop/scale them as needed when rendering. Check matte edges, foreground colour and final eye-line against the real speaker footage. Native dimensions are recorded in the manifest; the files have not been upscaled to video delivery dimensions.

## Implementation handoff

Claude owns speaker sizing, placement, cropping, camera switching, any additional blur/colour matching, captions and renderer integration. The old episode background files `assets/bg_milad.png` and `assets/bg_hooman.png` have not been replaced. `render_poc.py` currently loads those through `compose_person()`; `shorts.py` uses the same helpers. Wire these new plates explicitly rather than assuming the renderer already uses them.

The user approved both speaker plates with “ok store these.” on 2026-09-28. Preserve them as the selected background assets; the manifest records their original checksums. Do not reuse the rejected equal-box Zoom-style layout. Logo and opening-animation approvals are recorded separately in `DECISIONS.md`; approved identity packages remain unchanged.
