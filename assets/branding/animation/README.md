# Peyvand opening animation — version 1

Created 2026-09-28 following “ok do it.” Approved and saved following “cool save it.” This is the version 1 motion and sonic-signature baseline; the approved logo kit remains unchanged.

## Watch

Open `preview.html` to compare versions with playback controls. Each MP4 runs 2.8 seconds at 30 fps (84 frames), encoded as H.264 with a fast-start header.

| Layout | Size | Colour variants |
|---|---|---|
| Landscape | 1920 × 1080 | Light and dark |
| Vertical | 1080 × 1920 | Light and dark |

Files ending in `-silent.mp4` contain no audio stream. Other MP4 files contain the sonic signature. Posters show the final hold. Full package: `../peyvand-animation-v1.zip`.

## Motion

The original left stroke enters at 0.08s; the right answers at 0.36s. Both ease into their exact master positions by 1.06s. The complete Persian wordmark rises slightly and fades in from 1.12–1.58s, then holds until 2.8s. All lettering, dots, counters and relative proportions come directly from the approved master paths. Movement uses cubic easing without overshoot. Colours remain `#15181B` and `#E9ECEF`.

## Sound

`audio/peyvand-sonic-signature.wav` is the finished 48 kHz stereo, 24-bit PCM cue. Generated with ElevenLabs Sound Effects v2; take 3 supplies this first edit because its measured attacks at approximately 0.13s and 0.50s align with the two entrances. The retained four MP3 takes and `audio/generation-notes.json` preserve provenance and alternatives. The user approved this delivered sonic signature with “cool save it”; the other takes remain alternatives. The WAV is converted from the generated MP3, not an original lossless recording.

Sample peak is normalized to -4.5 dBFS, with short edge fades and a clean 2.8-second padded ending. Sound-on videos encode it as 192 kbps AAC. Use the silent exports when applying a separate audio mix.

## Rebuild

In the Peyvand repository run:

```sh
.venv/bin/python scripts/render_logo_animation.py
```

Requires Python 3, `rsvg-convert`, FFmpeg and FFprobe. No external Python packages are needed. `--mux-only` reprocesses the retained audio, remuxes existing silent videos, checks exports and rebuilds the ZIP. The ZIP's `source/` includes the rendering script and SVG master for reference; its script expects the repository layout documented above. `timeline.json` records the motion values used by this version.

`validation.json` records dimensions, frame count, duration, audio-stream presence, complete video decoding, unchanged approved-kit checksums and identical final vector geometry. Final posters and intermediate motion frames were visually inspected. Videos are saved locally; the repository's existing global MP4 ignore rule still applies. The ZIP retains the complete deliverable.
