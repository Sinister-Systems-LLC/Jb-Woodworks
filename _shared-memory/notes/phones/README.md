> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Per-phone state notes

One markdown file per phone, named by ADB serial:

```
<SERIAL>.md
```

Each file tracks that phone's installed modules, current proxy, last
attestation, owner agent, and an append-only activity log. Read **before**
any push; update **after**.

This directory is referenced by:

- `D:\Sinister Sanctum\tools\sinister-phone-viewer\viewer.py`
  (`get_phone_state`, `push_frida_to`, `adb_push_file`)
- The Sanctum Console **Devices** tab
- `D:\Sinister Sanctum\_shared-memory\notes\2026-05-19-adb-phone-containerization.md`
  (the standing rule on per-phone containerization)

Template fields:

```markdown
# Phone: <SERIAL> (label: P1 / P2 / ...)

**OS:** Android 14, KernelSU 0.7.0
**Attestation:** Yurikey51 (expires 2026-05-24)
**Last connected:** YYYY-MM-DD HH:MM
**Owner agent:** snap-emu / tiktok-emu / master
**Installed modules:**
  - frida-server-15.x (pushed 2026-05-18, /data/local/tmp/frida-server)
**Current proxy:** none / 192.168.1.50:8080

## Activity log

- YYYY-MM-DD HH:MM — first attached / frida pushed / proxy set / ...
```
