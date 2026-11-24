#!/usr/bin/env python3
"""STAGE SYNTH F1 evidence screening; NOT a piano-identification or physical fidelity certification.

Source audio never enters synthesis or this repository. A structurally complete
bundle remains READY_FOR_MANUAL_REVIEW until independent verification and owner approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import wave

EXPECTED_MODEL = "Yamaha C3X"
REQUIRED_DYNAMICS = {"pp", "mf", "ff"}
REQUIRED_MEASURES = {
    "C4_string_count": "count",
    "C4_vibrating_length": "m",
    "C4_wire_diameter": "m",
    "C4_linear_density": "kg/m",
    "C4_tension": "N",
    "C4_inharmonicity_B": "1",
    "C4_partial_decay": "1/s",
    "C4_strike_position": "fraction_L",
}
LIMITS = {
    "C4_string_count": (1, 4),
    "C4_vibrating_length": (0.05, 2.5),
    "C4_wire_diameter": (0.0002, 0.003),
    "C4_linear_density": (0.0001, 0.1),
    "C4_tension": (30, 4000),
    "C4_inharmonicity_B": (0, 0.02),
    "C4_partial_decay": (0, 100),
    "C4_strike_position": (0.01, 0.3),
}
SHA256 = re.compile(r"^[a-f0-9]{64}$")


def _valid_sha(s):
    return isinstance(s, str) and SHA256.fullmatch(s) is not None


def _verified_asset(asset: dict, root: Path, problems: list, prefix: str, *, wav=False):
    """Check content hash and prohibit traversal/symlink escape. No network or side effects."""
    path = asset.get("path")
    expected = asset.get("sha256")
    if not isinstance(path, str) or not path.strip():
        problems.append(f"{prefix}: arquivo não informado")
        return
    if not _valid_sha(expected):
        problems.append(f"{prefix}: SHA-256 ausente/inválido")
        return
    fragment = Path(path)
    if fragment.is_absolute() or any(part == ".." for part in fragment.parts):
        problems.append(f"{prefix}: caminho externo/relativo inseguro")
        return
    candidate = (root / fragment).resolve()
    if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
        problems.append(f"{prefix}: arquivo ausente/fora do acervo")
        return
    with candidate.open("rb") as f:
        h = hashlib.file_digest(f, "sha256").hexdigest()
    if h != expected:
        problems.append(f"{prefix}: SHA-256 diferente do arquivo real")
        return
    if wav:
        try:
            with wave.open(str(candidate), "rb") as f:
                if f.getframerate() < 44100 or f.getnchannels() not in (1, 2) or f.getsampwidth() not in (2, 3, 4) or f.getnframes() < 44100:
                    problems.append(f"{prefix}: WAV PCM inválido para avaliação F1")
        except (wave.Error, EOFError, OSError):
            problems.append(f"{prefix}: o arquivo não é WAV PCM legível")


def evaluate(bundle: dict, root: Path) -> dict:
    problems = []
    if bundle.get("schema") != "stage-c3x-f1-evidence-v1":
        problems.append("schema de evidências não reconhecido")
    instr = bundle.get("instrument", {})
    if instr.get("manufacturer") != "Yamaha" or instr.get("model") != "C3X":
        problems.append("exemplar não é Yamaha C3X convencional")
    exemplar = instr.get("exemplar_id")
    if not isinstance(exemplar, str) or len(exemplar.strip()) < 4 or exemplar.lower().strip() in {"unknown", "example", "placeholder", "c3x", "teste"}:
        problems.append("exemplar real individual não identificado")
    for k in ("recording_session", "tuning_reference_hz", "microphone_geometry", "room_description", "lid_position"):
        if not instr.get(k):
            problems.append(f"metadado do instrumento incompleto: {k}")
    if instr.get("test_fixture") is not False:
        problems.append("pacote sintético/de teste não constitui evidência física")
    rights = bundle.get("rights", {})
    if rights.get("commercial_analysis_authorized") is not True or rights.get("permission_checked_by_human") is not True:
        problems.append("permissão comercial e conferência humana não confirmadas")
    if not isinstance(rights.get("permission_reference"), str) or len(rights.get("permission_reference", "").strip()) < 8:
        problems.append("referência da autorização ausente")
    recordings = bundle.get("recordings", [])
    seen, ids = set(), set()
    for index, rec in enumerate(recordings):
        loc = f"gravação {index+1}"
        dynamic = rec.get("dynamic")
        if dynamic in seen:
            problems.append(f"{loc}: dinâmica duplicada")
        seen.add(dynamic)
        if rec.get("midi_note") != 60 or rec.get("instrument_id") != exemplar:
            problems.append(f"{loc}: não é Dó4 do mesmo exemplar")
        if rec.get("processed") is not False or rec.get("pedal") != "off" or rec.get("held_key") is not True:
            problems.append(f"{loc}: sinal processado, pedal ou tecla sem condição definida")
        asset=rec.get("asset", {})
        _verified_asset(asset, root, problems, loc, wav=True)
        ids.add(asset.get("sha256"))
    if not REQUIRED_DYNAMICS.issubset(seen):
        problems.append("faltam gravações originais Dó4 pp/mf/ff")
    if len(ids) < 3:
        problems.append("as três dinâmicas devem possuir registros originais distintos")
    measures = bundle.get("measurements", [])
    found = set()
    independently_measured = set()
    for j, m in enumerate(measures):
        k = m.get("parameter")
        prefix=f"medição {j+1} ({k})"
        if k in found:
            problems.append(f"{prefix}: parâmetro duplicado")
        found.add(k)
        if k not in REQUIRED_MEASURES:
            continue
        if m.get("instrument_id") != exemplar:
            problems.append(f"{prefix}: outro instrumento")
        if m.get("unit") != REQUIRED_MEASURES[k]:
            problems.append(f"{prefix}: unidade incorreta")
        if k == "C4_string_count" and (isinstance(m.get("value"), bool) or not isinstance(m.get("value"), int)):
            problems.append(f"{prefix}: contagem de cordas deve ser inteiro")
        v = m.get("value"); u = m.get("standard_uncertainty")
        if isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v) or not (LIMITS[k][0] < v < LIMITS[k][1]):
            problems.append(f"{prefix}: valor numérico inválido ou fisicamente suspeito")
        if isinstance(u, bool) or not isinstance(u, (int,float)) or not math.isfinite(u) or u <= 0:
            problems.append(f"{prefix}: incerteza deve ser positiva e finita")
        if not m.get("method") or not m.get("provenance") or m.get("source_type") != "real_measurement":
            problems.append(f"{prefix}: método/proveniência/medição real ausente")
        if m.get("independent_of_target_frequency") is True:
            independently_measured.add(k)
        _verified_asset(m.get("source_asset", {}), root, problems, prefix)
    for k in REQUIRED_MEASURES.keys() - found:
        problems.append(f"parâmetro físico C4 obrigatório ausente: {k}")
    if not ({"C4_linear_density", "C4_tension"} & independently_measured):
        problems.append("densidade linear e tensão não podem ser ambas derivadas da frequência alvo")
    # This is a screening gate, never a scientific or commercial approval by itself.
    status="BLOCKED" if problems else "READY_FOR_MANUAL_REVIEW"
    return {"schema":"stage-c3x-f1-evidence-review-v1", "status":status,
            "automatic_approval":False, "C3X_F1_approved":False,
            "human_owner_signoff_required":True, "physical_C3X_measurements_verified_by_tool":False,
            "missing_or_invalid":sorted(set(problems)),
            "recording_count":len(recordings), "measurement_count":len(measures),
            "message":"Mesmo READY_FOR_MANUAL_REVIEW exige verificação independente, licenças e aceite explícito do titular."}


def inspect_project_state(path: Path) -> dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    status="BLOCKED" if x.get("status")!="CONCLUIDA" or x.get("physical_c4_measured_count",0)==0 or x.get("physical_c4_audio_acquired_count",0)==0 or x.get("commercial_licenses_confirmed_for_f1_C4_audio",0)==0 else "NEEDS_INDEPENDENT_REVIEW"
    return {"status":status,"automatic_approval":False,"C3X_F1_approved":False,"physical_c4_measured_count":x.get("physical_c4_measured_count",0),"physical_c4_audio_acquired_count":x.get("physical_c4_audio_acquired_count",0),"commercial_licenses_confirmed_for_f1_C4_audio":x.get("commercial_licenses_confirmed_for_f1_C4_audio",0),"reference_target":x.get("reference_target")}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--bundle",type=Path,help="manifesto de evidências efetivamente coletadas")
    mode.add_argument("--project-state",type=Path,help="estado F1 arquivado no repositório")
    ap.add_argument("--root",type=Path,default=Path("."),help="raiz das evidências (sem rede)")
    ap.add_argument("--expect-blocked",action="store_true",help="para testes de CI: passa APENAS se o F1 continuar bloqueado")
    ap.add_argument("--output",type=Path,help="salvar relatório JSON")
    a=ap.parse_args(argv)
    try:
        result=inspect_project_state(a.project_state) if a.project_state else evaluate(json.loads(a.bundle.read_text(encoding="utf-8")),a.root)
    except (OSError,ValueError,TypeError) as exc:
        print(json.dumps({"status":"ERROR","error":str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2
    output=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    print(output,end="")
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(output,encoding="utf-8")
    if a.expect_blocked:
        return 0 if result["status"]=="BLOCKED" else 1
    return 0 if result["status"]=="READY_FOR_MANUAL_REVIEW" else 1


if __name__=="__main__":
    raise SystemExit(main())
