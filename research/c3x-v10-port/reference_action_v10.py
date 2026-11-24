"""Compare exact Python V10 reference action without importing offline SciPy DSP."""
import importlib.util
import json
import pathlib
import sys
import types

base = pathlib.Path(__file__).resolve().parents[1] / "c3x-python" / "v10" / "stage_synth_c3x"
package = types.ModuleType("stage_synth_c3x")
package.__path__ = [str(base)]
sys.modules["stage_synth_c3x"] = package
for component in ("action", "continuous_action"):
    fullname = "stage_synth_c3x." + component
    spec = importlib.util.spec_from_file_location(fullname, base / (component + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
from stage_synth_c3x.continuous_action import schedule_continuous_action, ContinuousActionConfig
payload = json.load(sys.stdin)
config = ContinuousActionConfig(**payload.get("config", {}))
scheduled, diagnostics = schedule_continuous_action(
    payload.get("events", []), payload.get("length", 1.0),
    keyframes=payload.get("keyframes", None),
    config=config, mode=payload.get("mode", "double"),
    include_trajectories=payload.get("includeTrajectories", False))
print(json.dumps({"scheduled":scheduled,"diagnostics":diagnostics}))
