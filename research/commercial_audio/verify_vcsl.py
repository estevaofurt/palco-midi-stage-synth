#!/usr/bin/env python3
"""Stage Synth: verify ORIGINAL CC0 VCSL WAV files, no DSP and no audio artifacts.

The checked-in manifest pins individual file identities to source Git blob SHA1
and source commit. Original bytes are downloaded ONLY to a runner /tmp folder.
Emits metadata plus SHA256, never samples or features that reconstruct audio.

Usage:
  STAGE_COMMERCIAL_AUDIO_DIR=/tmp/stage-safe-reference \
    python3 research/commercial_audio/verify_vcsl.py \
      research/commercial_audio/vcsl_cc0_pilot_manifest.json \
      /tmp/stage-safe-reference/verified.json

Acquisition is an explicitly controlled *research preparation* task, not a
license finding, calibration, training, or integration approval.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import urllib.parse
import urllib.request
import wave


MAX_SINGLE_FILE = 18_000_000
MAX_TOTAL = 70_000_000
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SAFE_ID_RE = re.compile(r"^[a-z0-9-]{3,100}$")


def source_url(repository: str, commit: str, file_path: str) -> str:
    if repository != "sgossner/VCSL":
        raise ValueError("unexpected source repository")
    if not GIT_SHA_RE.fullmatch(commit):
        raise ValueError("source commit must be immutable SHA1")
    p = PurePosixPath(file_path)
    if p.is_absolute() or ".." in p.parts or "\\" in file_path or not file_path.endswith(".wav"):
        raise ValueError("unsafe source path")
    if not file_path.startswith("Chordophones/Zithers/"):
        raise ValueError("not a vetted piano sample path")
    # Quote path components, leaving the directory separators, including '#' and spaces.
    return "https://raw.githubusercontent.com/" + repository + "/" + commit + "/" + urllib.parse.quote(file_path, safe="/")


def check_manifest(manifest: dict) -> None:
    if manifest.get("schema") != "stage-commercial-reference-manifest-v1":
        raise ValueError("unexpected manifest schema")
    origin = manifest.get("origin") or {}
    if origin.get("repository") != "sgossner/VCSL" or origin.get("repoLicense") != "CC0-1.0":
        raise ValueError("source must have reviewed CC0 license and pinned VCSL")
    if not GIT_SHA_RE.fullmatch(origin.get("commit", "")):
        raise ValueError("missing immutable VCSL commit")
    items = manifest.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 12:
        raise ValueError("require 1..12 files")
    if sum(x.get("bytes", 0) for x in items) > MAX_TOTAL:
        raise ValueError("total sample budget exceeded")
    seen = set()
    for item in items:
        if not SAFE_ID_RE.fullmatch(item.get("id", "")):
            raise ValueError("bad candidate id")
        if item["id"] in seen:
            raise ValueError("duplicate candidate id")
        seen.add(item["id"])
        if not isinstance(item.get("bytes"), int) or not 100_000 <= item["bytes"] <= MAX_SINGLE_FILE:
            raise ValueError("invalid sample size")
        if not GIT_SHA_RE.fullmatch(item.get("gitBlobSha", "")):
            raise ValueError("missing Git blob hash")
        source_url(origin["repository"], origin["commit"], item["path"])


def fetch_and_verify(item: dict, origin: dict, workdir: Path) -> dict:
    url = source_url(origin["repository"], origin["commit"], item["path"])
    dest = workdir / (item["id"] + ".wav")
    git_blob = hashlib.sha1()
    git_blob.update(f"blob {item['bytes']}\0".encode("ascii"))
    sha256 = hashlib.sha256()
    total = 0
    req = urllib.request.Request(url, headers={"User-Agent": "StageSynthCommercialReferenceAudit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as stream, dest.open("wb") as out:
            while chunk := stream.read(256 * 1024):
                total += len(chunk)
                if total > item["bytes"] or total > MAX_SINGLE_FILE:
                    raise ValueError("file larger than reviewed manifest")
                out.write(chunk)
                sha256.update(chunk)
                git_blob.update(chunk)
        if total != item["bytes"]:
            raise ValueError("size mismatch")
        if git_blob.hexdigest() != item["gitBlobSha"]:
            raise ValueError("Git blob SHA mismatch: source file or contents changed")
        with wave.open(str(dest), "rb") as snd:
            info = {
                "sampleRate": snd.getframerate(),
                "channels": snd.getnchannels(),
                "sampleWidthBits": snd.getsampwidth() * 8,
                "frames": snd.getnframes(),
                "seconds": round(snd.getnframes() / snd.getframerate(), 6),
                "compression": snd.getcomptype()
            }
        if info["sampleRate"] not in (44100, 48000, 96000):
            raise ValueError("unexpected WAV sample rate")
        if not 1 <= info["channels"] <= 2 or info["sampleWidthBits"] not in (16, 24, 32):
            raise ValueError("unsupported WAV encoding")
        if info["frames"] < info["sampleRate"] // 5 or info["compression"] != "NONE":
            raise ValueError("bad, compressed or near-empty WAV")
        return {
            "id": item["id"], "instrument": item["instrument"],
            "recordedPitch": item["recordedPitch"], "midi": item["midi"],
            "velocityLayer": item["velocityLayer"], "capture": item["capture"],
            "sourceCommit": origin["commit"], "sourcePath": item["path"],
            "sourceUrl": url, "sourceGitBlobSha": item["gitBlobSha"],
            "sha256": sha256.hexdigest(), "bytes": total, "wav": info,
            "timbreOnly": True,
            "velocityPhysicallyCalibrated": False,
            "processingKnown": item["sourceProcessing"],
            "verified": True
        }
    finally:
        # Even successful samples are never retained beyond the verification step.
        dest.unlink(missing_ok=True)


def main(argv: list[str]) -> None:
    if len(argv) != 3:
        raise SystemExit("usage: verify_vcsl.py <manifest.json> <metadata-report.json>")
    manifest = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    check_manifest(manifest)
    root = os.environ.get("STAGE_COMMERCIAL_AUDIO_DIR")
    if not root or not Path(root).resolve().is_relative_to(Path("/tmp").resolve()):
        raise ValueError("STAGE_COMMERCIAL_AUDIO_DIR must be a private /tmp directory")
    workdir = Path(root).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "stage-commercial-reference-verification-v1",
        "source": manifest["origin"],
        "limitations": manifest["sourceCaveats"],
        "notes": "Original WAV never uploaded; data is metadata and one-way checksums. CC0 eligibility is separate from acoustic suitability.",
        "verified": []
    }
    for item in manifest["items"]:
        result = fetch_and_verify(item, manifest["origin"], workdir)
        report["verified"].append(result)
        print(f"VERIFIED {result['id']}: {result['bytes']} bytes {result['wav']['sampleRate']}Hz/"
              f"{result['wav']['sampleWidthBits']}bit SHA256={result['sha256']}")
    output = Path(argv[2]).resolve()
    if output.parent != workdir:
        raise ValueError("report output must be in /tmp workdir")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(report['verified'])} ORIGINAL WAV files; report has metadata only. No samples persist.")


if __name__ == "__main__":
    main(sys.argv)
