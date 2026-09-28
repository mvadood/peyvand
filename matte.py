"""Person matting with RobustVideoMatting: writes a grayscale alpha video for a source clip.

usage: matte.py SRC OUT START DURATION [WIDTH HEIGHT]
"""
import subprocess, sys, time
import numpy as np, torch

sys.path.insert(0, "work/rvm")
from model import MattingNetwork

FF = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
src, out, start, dur = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
W, H = (int(sys.argv[5]), int(sys.argv[6])) if len(sys.argv) > 6 else (1920, 1080)

dev = "mps"
model = MattingNetwork("resnet50").eval().to(dev)
model.load_state_dict(torch.load("work/rvm_resnet50.pth", map_location=dev))

reader = subprocess.Popen([FF, "-v", "error", "-ss", str(start), "-t", str(dur), "-i", src,
                           "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
writer = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                           "-c:v", "libx264", "-crf", "8", "-preset", "fast", "-pix_fmt", "gray", out], stdin=subprocess.PIPE)
rec = [None] * 4
n, t0, fsize = 0, time.time(), W * H * 3
with torch.no_grad():
    while True:
        buf = reader.stdout.read(fsize)
        if len(buf) < fsize:
            break
        x = torch.from_numpy(np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()).to(dev).permute(2, 0, 1)[None].float() / 255
        fgr, pha, *rec = model(x, *rec, downsample_ratio=0.25)
        writer.stdin.write((pha[0, 0] * 255).clamp(0, 255).byte().cpu().numpy().tobytes())
        n += 1
        if n % 300 == 0:
            print(f"{out}: {n} frames, {n / (time.time() - t0):.1f} fps", flush=True)
writer.stdin.close(); writer.wait()
print(f"done {out}: {n} frames in {time.time() - t0:.0f}s")
