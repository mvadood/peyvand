# Peyvand (پیوند)

Tooling for a Persian-language series of conversations about books: long-form YouTube episodes,
podcast audio, and vertical clips for YouTube Shorts / Instagram Reels.

Episode 1: *Are Your Lights On?* (Donald C. Gause & Gerald M. Weinberg).

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
| v1 cut | `edit.py` | First draft (ffmpeg-only, no background replacement) |

## Setup

```bash
brew install ffmpeg-full
python3 -m venv .venv
.venv/bin/python -m pip install mlx-whisper torch torchvision opencv-python-headless pillow numpy av tqdm pims
git clone --depth 1 https://github.com/PeterL1n/RobustVideoMatting.git work/rvm
curl -L -o work/rvm_resnet50.pth https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_resnet50.pth
```

Source recordings, transcripts, mattes and renders are not in git.
