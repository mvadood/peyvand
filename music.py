"""Placeholder music bed (synthesised, license-free): warm pad + soft piano arpeggio.
Swap assets/music.wav for a real track later."""
import numpy as np, wave

SR, BPM = 48000, 72
beat = 60 / BPM
bar = 4 * beat
rng = np.random.default_rng(1)

def midi(n):
    return 440 * 2 ** ((n - 69) / 12)

# Am9 - Fmaj7 - Cmaj7 - G6, voiced around middle C
CHORDS = [[45, 57, 60, 64, 67, 71], [41, 57, 60, 64, 65, 69], [48, 55, 59, 64, 67, 72], [43, 55, 59, 62, 64, 71]]
BARS = 16
N = int(BARS * bar * SR)
out = np.zeros((N, 2))
t_all = np.arange(N) / SR

def pad(freq, start, dur, amp):
    n = int(dur * SR); t = np.arange(n) / SR
    env = np.minimum(1, t / 1.2) * np.minimum(1, (dur - t) / 1.5).clip(0)
    sig = sum(np.sin(2 * np.pi * freq * (1 + d) * t + rng.uniform(0, 6)) / (k + 1) ** 1.5
              for k, d in enumerate((0, 0.003, -0.004, 1.0, 2.0)))
    s0 = int(start * SR)
    seg = out[s0 : s0 + n]
    pan = rng.uniform(0.3, 0.7)
    seg[:, 0] += sig[: len(seg)] * env[: len(seg)] * amp * (1 - pan)
    seg[:, 1] += sig[: len(seg)] * env[: len(seg)] * amp * pan

def piano(freq, start, amp):
    dur = 3.0; n = int(dur * SR); t = np.arange(n) / SR
    env = np.exp(-t * 2.2) * np.minimum(1, t / 0.004)
    sig = sum(np.sin(2 * np.pi * freq * k * t) * np.exp(-t * k * 0.8) / k ** 1.3 for k in (1, 2, 3, 4))
    s0 = int(start * SR)
    seg = out[s0 : s0 + n]
    pan = 0.35 + 0.3 * (freq > 400)
    seg[:, 0] += sig[: len(seg)] * env[: len(seg)] * amp * (1 - pan)
    seg[:, 1] += sig[: len(seg)] * env[: len(seg)] * amp * pan

for b in range(BARS):
    ch = CHORDS[b % 4]
    t0 = b * bar
    for n in ch:
        pad(midi(n), t0, bar + 1.2, 0.05)
    pad(midi(ch[0] - 12), t0, bar + 1.0, 0.07)
    if b >= 1:  # arpeggio enters after the first bar
        pattern = [ch[1] + 12, ch[3] + 12, ch[4] + 12, ch[5] + 12, ch[4] + 12, ch[3] + 12, ch[2] + 12, ch[3] + 12]
        for i, n in enumerate(pattern):
            piano(midi(n), t0 + i * beat / 2 + rng.uniform(0, 0.012), 0.10 * (0.8 + 0.2 * (i % 2 == 0)))

# simple stereo reverb: feedback delays
rev = np.zeros_like(out)
for d, g in ((0.037, 0.5), (0.053, 0.45), (0.071, 0.4), (0.097, 0.35), (0.131, 0.3)):
    k = int(d * SR)
    tmp = out.copy()
    for _ in range(6):
        tmp = np.vstack([np.zeros((k, 2)), tmp[:-k]]) * g
        rev += tmp[:, ::-1] * 0.35
mix = out + rev
mix /= np.abs(mix).max() / 0.8
# loop-friendly: short fades at the ends
f = int(0.5 * SR)
mix[:f] *= np.linspace(0, 1, f)[:, None]; mix[-f:] *= np.linspace(1, 0, f)[:, None]
with wave.open("assets/music.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print(f"assets/music.wav {N / SR:.1f}s")
