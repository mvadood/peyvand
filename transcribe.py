import json, sys, mlx_whisper
src, out = sys.argv[1], sys.argv[2]
r = mlx_whisper.transcribe(src, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", word_timestamps=True, condition_on_previous_text=False, language="fa")
json.dump(r, open(out, "w"))
print("done", out, len(r["segments"]))
