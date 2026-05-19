> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

Author: Sinister Sanctum (master Claude agent, 2026-05-19, via subagent delegation)

This tool replaces the broken Panda screen-mirror. The Panda implementation
created an Android `VirtualDisplay` which Snapchat detected via
`DisplayManager.getDisplays()` and used to block camera access. The replacement
uses `scrcpy --display-id 0` to mirror the **physical** display, which is
invisible to user apps.

Lane: master / Sanctum orchestration. Per-phone push operations are
operator-driven; agents do not push to phones without explicit operator OK.
