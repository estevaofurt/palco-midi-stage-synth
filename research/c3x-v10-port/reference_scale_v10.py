"""Extract original Python V10 estimated string scale and tuning, without DSP."""
import importlib.util
import json
import pathlib
import sys
import types

base = pathlib.Path(__file__).resolve().parents[1] / "c3x-python" / "v10" / "stage_synth_c3x"
package = types.ModuleType("stage_synth_c3x")
package.__path__ = [str(base)]
sys.modules["stage_synth_c3x"] = package
for component in ("parameters", "tuning"):
    fullname = "stage_synth_c3x." + component
    spec = importlib.util.spec_from_file_location(fullname, base / (component + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
from stage_synth_c3x.parameters import note_params
from stage_synth_c3x.tuning import tune_note, note_partials, tuning_cents, anchor_stretch_cents

payload = json.load(sys.stdin)
out = []
for midi in payload.get("notes", list(range(21, 109))):
    params = vars(note_params(midi)).copy()
    params.pop("origem", None)
    profiles = {}
    for profile in ("equal", "stretch_experimental"):
        profiles[profile] = {
            "tuning": vars(tune_note(midi, profile)),
            "partials": note_partials(midi, profile, 12).tolist(),
            "cents": tuning_cents(midi, profile),
        }
    out.append({"params": params, "profiles": profiles})
print(json.dumps({"notes": out, "anchors": anchor_stretch_cents()}))
