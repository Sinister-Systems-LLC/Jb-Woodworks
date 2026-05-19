import json, sys, importlib.util, pathlib
sys.path.insert(0, str(pathlib.Path(sys.argv[1]).parent))
spec = importlib.util.spec_from_file_location("custodian_server", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
action = sys.argv[2]
if action == "snapshot":
    print(json.dumps(mod.snapshot_now.fn() if hasattr(mod.snapshot_now, "fn") else mod.snapshot_now()))
elif action == "cleanup":
    print(json.dumps(mod.cleanup.fn() if hasattr(mod.cleanup, "fn") else mod.cleanup()))
else:
    print(json.dumps({"error": f"unknown action: {action}"}))
