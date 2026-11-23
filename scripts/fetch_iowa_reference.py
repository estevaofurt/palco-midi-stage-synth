#!/usr/bin/env python3
"""Fetch a small, public, single-note subset of the University of Iowa Steinway B.
Raw AIFF and decoded PCM stay in RUNNER_TEMP. Publish metadata/results only.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

SOURCES = [
    "https://theremin.music.uiowa.edu/sound%20files/MIS/Piano_Other/piano/",
    "https://huggingface.co/datasets/sondalex/university-iowa-piano-samples/resolve/main/university_iowa/",
]
NOTES = {"C2": 36, "C4": 60, "C6": 84}
LEVELS = ("pp", "mf", "ff")
# Support a first pilot without altering source or needing CLI inputs.
selected = os.environ.get("STAGE_PIANO_SELECTION", "C4:mf")
if selected == "matrix":
    jobs = [(pitch, velocity) for pitch in NOTES for velocity in LEVELS]
else:
    jobs = []
    for item in selected.split(","):
        pitch, velocity = item.strip().split(":")
        if pitch not in NOTES or velocity not in LEVELS:
            raise ValueError("Unexpected pitch/dynamic; accepted C2/C4/C6 and pp/mf/ff")
        jobs.append((pitch, velocity))

directory = Path(os.environ["STAGE_AUDIO_WORKDIR"]).resolve()
directory.mkdir(parents=True, exist_ok=True)
manifest = {"notes": []}

def fetch_one(name, output):
    errors = []
    for root in SOURCES:
        url = root + name
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, headers={"User-Agent":"StageSynthAcousticResearch/1.0"})
                sha = hashlib.sha256()
                size = 0
                with urllib.request.urlopen(req, timeout=35) as reader, output.open("wb") as writer:
                    while chunk := reader.read(1024 * 256):
                        size += len(chunk)
                        if size > 20_000_000:
                            raise RuntimeError("Refusing to download oversized reference audio (>20 MB)")
                        sha.update(chunk)
                        writer.write(chunk)
                if size < 100_000 or output.read_bytes()[:4] != b"FORM":
                    raise RuntimeError("Response is not a plausible AIFF recording")
                return url, sha.hexdigest(), size
            except Exception as e:
                errors.append(f"{url}: {type(e).__name__}: {str(e)[:150]}")
                output.unlink(missing_ok=True)
                if attempt == 0:
                    time.sleep(1)
    raise RuntimeError("Reference download failed:\n" + "\n".join(errors))

for pitch, velocity in jobs:
    filename = f"Piano.{velocity}.{pitch}.aiff"
    original = directory / filename
    url, sha256, size = fetch_one(filename, original)
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate,channels,codec_name", "-of", "json", str(original)
    ]))
    if not probe.get("streams"):
        raise RuntimeError(f"Not an audio file: {filename}")
    info = probe["streams"][0]
    mono_pcm = directory / f"{pitch}_{velocity}.f32le"
    subprocess.run([
        "ffmpeg", "-v", "error", "-nostdin", "-y", "-i", str(original),
        "-map", "0:a:0", "-ar", "48000", "-ac", "1",
        "-f", "f32le", "-acodec", "pcm_f32le", str(mono_pcm)
    ], check=True)
    manifest["notes"].append({
        "id": f"iowa-steinway-model-b-{pitch}-{velocity}",
        "instrument": "Steinway Model B (University of Iowa)",
        "key": NOTES[pitch],
        "dynamic": velocity,
        "stageCharacter": "american",
        "pcmPath": str(mono_pcm),
        "originalUrl": url,
        "sha256": sha256,
        "bytes": size,
        "originalRate": int(info["sample_rate"]),
        "originalChannels": int(info["channels"]),
        "originalFormat": info.get("codec_name"),
        "captureNotes": "Steinway B, 2001, Neumann KM84 8in over strings, non-anechoic, pp/mf/ff musical dynamics"
    })
    print("Fetched", filename, size, "bytes", "SHA256", sha256[:16], "source", url, flush=True)

(directory / "manifest.json").write_text(json.dumps(manifest, indent=2),encoding="utf-8")
print(f"Ready for private on-runner analysis: {len(jobs)} recordings (none staged for Git)")
