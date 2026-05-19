# Sanctum Library

This is the **auto-curated archive** populated by the **md-trash-bin sweeper**.

Subfolders are **topics** (snap / tiktok / panel / kernel / signing / api / ui /
ops / security / idea / misc). Files inside each topic folder follow the shape:

```
YYYY-MM-DD-<slug>.md
```

Each file begins with the original title heading, immediately followed by an
auto-injected line of the form:

```
**Auto-categorized:** YYYY-MM-DD HH:MM by md-trash-bin sweeper.
```

---

## Rules of engagement

- **Operators and agents may READ from this folder freely.**
- **Do NOT manually drop files here.** If you have a new note, drop it in
  `C:\Users\Zonia\Desktop\MD-Trash-Bin\` and let the sweeper place it.
  Manual drops break the archive's guarantees (slug normalization, dedupe,
  timestamp prepending, manifest accounting).
- **You may promote** a file out of `misc/` into a better topic folder
  by moving it manually — but ideally edit the topic map in
  `D:\Sinister Sanctum\automations\sweep-md-trash.ps1` so future sweeps catch
  the same pattern.
- **Manifests** of every sweep are kept in `_manifests/sweep-*.json` —
  do not delete them; they are the audit trail.

---

## Layout

```
library/
  _manifests/
    sweep-2026-05-19-1430.json
    sweep-2026-05-19-2030.json
    ...
  snap/
  tiktok/
  panel/
  kernel/
  signing/
  api/
  ui/
  ops/
  security/
  idea/
  misc/
```

Topic folders are created on demand — they only exist after the first file
of that topic lands.

---

## See also

- Trash bin (drop here): `C:\Users\Zonia\Desktop\MD-Trash-Bin\`
- Manual sweep trigger: `C:\Users\Zonia\Desktop\Sweep-MD-Trash.bat`
- Sweeper source:       `D:\Sinister Sanctum\automations\sweep-md-trash.ps1`
- Scheduled-task installer (run once, elevated):
  `D:\Sinister Sanctum\automations\install-md-sweep-task.ps1`
- Tool card:            `D:\Sinister Sanctum\tools\md-trash-bin\README.md`
