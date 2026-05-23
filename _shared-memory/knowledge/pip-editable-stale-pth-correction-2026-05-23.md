<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# pip-show says installed ≠ import works (stale .pth correction)

**Status:** correction 2026-05-23T08:30Z — addendum to `pip-editable-hides-mcp-cwd-emptiness-2026-05-23.md`.

**Trigger:** the sibling brain entry asserted *"`pip show sinister_apk_mcp` confirms it's editable-installed... `python -m sinister_apk_mcp` resolves the module via `sys.path`, not via cwd. The MCP launches fine"*. Empirical test showed otherwise on 2026-05-23T08:30Z.

## The pattern (one-liner correction)

**`pip show <name>` checks pip metadata. It does NOT check that the editable-install's target path still exists. Always run `python -c "import <module>"` as the ground-truth check.**

## Empirical anchor

2026-05-23T08:30Z verification on `sinister_apk_mcp`:

```
$ pip show sinister_apk_mcp
Name: sinister_apk_mcp
Version: 0.1.0
Location: C:\Users\Zonia\AppData\Roaming\Python\Python312\site-packages
Editable project location: C:\Users\Zonia\Desktop\Sinister-Snap-APK-\mcp-server
```

Looks fine. BUT:

```
$ ls "C:\Users\Zonia\Desktop\Sinister-Snap-APK-"
ls: cannot access — No such file or directory

$ python -c "import sinister_apk_mcp"
ModuleNotFoundError: No module named 'sinister_apk_mcp'
```

The `.pth` finder file at `site-packages/__editable___sinister_apk_mcp_0_1_0_finder.py` has hardcoded path:
```python
MAPPING: dict[str, str] = {'sinister_apk_mcp': 'C:\\Users\\Zonia\\Desktop\\Sinister-Snap-APK-\\mcp-server\\sinister_apk_mcp'}
```

Target directory doesn't exist → finder returns None → import fails. **pip-show still happily reports "installed" because pip only checks its own metadata, not whether the .pth target resolves.**

## Audit procedure (corrected)

When checking if a Python-launched MCP works:

1. `pip show <module>` — confirms pip thinks it's installed (necessary but not sufficient)
2. **`python -c "import <module>"`** — ground truth. If this fails, the install is broken regardless of pip-show.
3. If pip-show passes + import passes: GOOD
4. If pip-show passes + import fails: stale `.pth` — operator-action to either restore source at the editable-target path OR `pip uninstall + pip install -e <correct-path>` to retarget
5. If pip-show fails: not installed, fix with `pip install -e <path>`

## Sanctum-fleet residue (2026-05-23T08:30Z scan)

Five known-stale editable installs after this audit. Pip metadata reports them as installed but the editable-target path doesn't exist or is empty:

| Module | Reported editable-target | Reality | Recommended fix |
|---|---|---|---|
| sinister_apk_mcp | `C:\Users\Zonia\Desktop\Sinister-Snap-APK-\mcp-server` | path missing | operator: restore source OR `pip uninstall sinister_apk_mcp` and remove from .mcp.json |

(Audit covered 18 sinister-* + forge_memory_bridge + memory_graph_render + nano_banana + sanctum_backup; only `sinister_apk_mcp` failed the import check.)

## Anti-pattern

**Don't mark a queue row "RESOLVED" based on pip-show output alone.** Always verify the import. The 2026-05-23T08:20Z queue update at OPERATOR-ACTION-QUEUE.md prematurely marked sinister_apk_mcp resolved on pip-show evidence; the import still fails. Operator should treat that row as STILL OPEN.

## Composes with

- `pip-editable-hides-mcp-cwd-emptiness-2026-05-23` — the partial-truth this corrects. That entry is right that pip-editable resolves via sys.path (not cwd). It's wrong that pip-show alone proves the install works.
- `mcp-junction-fix-pattern-2026-05-23` — same family; both are about MCPs that look broken but might be fixable without `.mcp.json` edits. The pip-editable path is one such fix; junctions are another. Both fail when the underlying source is genuinely missing.
- `OPERATOR-ACTION-QUEUE.md` 2026-05-23 row "Decide on sinister_apk_mcp" — should be reopened.

## Reusable pattern

```python
# Bot/MCP install audit one-liner — use this, not just pip show
def install_works(module: str) -> bool:
    try:
        __import__(module)
        return True
    except ImportError:
        return False
```

Run that across the fleet on every Sanctum readiness audit. Pip metadata alone isn't ground truth.
