# Curator-specific gotchas

(Hand-edited. Universal gotchas at `09_REFERENCE/SANDBOX-GOTCHAS.md` are loaded automatically.)

- **Don't recommend extracting from `_archive/` or `old/` paths** - those are operator-archived; extraction would resurrect dead code.
- **Don't propose extracting Frida-bound helpers** if the absorbed facts list TT Frida-spawn as sandbox-blocked - the resulting library function would be unrunnable.
- **Skip leading-underscore names** (`_foo`, `__init__`) - they are private by convention.
