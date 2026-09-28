# Peyvand (پیوند)

Tooling for a Persian-language series of conversations about books: long-form YouTube episodes,
podcast audio, and vertical clips for YouTube Shorts / Instagram Reels.

Episode 1: *Are Your Lights On?* (Donald C. Gause & Gerald M. Weinberg).

Project and creative choices are recorded in the [decision log](DECISIONS.md).

The saved [music kit and Claude handoff](assets/branding/music-v1/README.md) provide five
Iranian/contemporary cues, source MP3s, editing WAVs and a provenance manifest. `short2.py` uses
them; the older `render_poc.py` / `shorts.py` renders still use the synthesized placeholder.

## Assets

| Folder | Contents |
|---|---|
| `assets/branding/` | Logo kit and vector master, opening animation + sonic signature, reading-room speaker plates, music kit v1, layout drafts, Vazirmatn font (OFL). Approvals and history are in `DECISIONS.md`. |
| `assets/episodes/01/broll/` | Generated illustrations for episode 1 with a [manifest](assets/episodes/01/broll/manifest.json) (style, generation IDs, cost). |
| `assets/*.png`, `assets/music.wav` | Graphics and placeholder music used by the POC renderers. |

## Pipeline

| Step | Script | What it does |
|---|---|---|
| Transcribe | `transcribe.py` | Whisper (mlx-whisper, `language="fa"`) per speaker, word timestamps |
| Speaker activity | `activity.py` | Per-track loudness → who is talking every 0.1s (`work/state.npy`) |
| Background matte | `matte.py` | RobustVideoMatting → grayscale alpha video per speaker |
| Backdrop | `make_bg.py` | Procedural studio backdrop (navy + warm bokeh) |
| Graphics | `graphics.py` | Road signs, tunnel scene, book/explainer cards (PIL + raqm for Persian) |
| Music | `music.py` | Synthesised placeholder bed (to be replaced by the series theme) |
| Long edit | `render_poc.py` | Shot plan, pause trimming, compositing, captions (ASS), audio mastering to -14 LUFS |
| Shorts | `shorts.py` + `shorts_cues.py` | 1080×1920 clips with hook title, chunked captions, graphics panels |
| Shorts v2 | `short2.py` | Illustration-led parking short: word-timed visual events, Ken Burns + dissolves, reading-room compositing (edge decontamination, light wrap, DOF), speaker bubble, quote/lesson cards, logo-animation end card, music kit mix |
| Covers | `make_covers.py` | 9:16 Reels/Shorts cover and 16:9 YouTube thumbnail |
| Logo | `scripts/` | Logo master, logo kit export and opening-animation renderer |
| v1 cut | `edit.py` | First draft (ffmpeg-only, no background replacement) |

## Setup

```bash
brew install ffmpeg-full librsvg
python3 -m venv .venv
.venv/bin/python -m pip install mlx-whisper torch torchvision opencv-python-headless pillow numpy av tqdm pims
git clone --depth 1 https://github.com/PeterL1n/RobustVideoMatting.git work/rvm
curl -L -o work/rvm_resnet50.pth https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_resnet50.pth
```

Source recordings, transcripts, mattes and renders are not in git.
