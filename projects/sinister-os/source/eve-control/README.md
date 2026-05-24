# source/eve-control/

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Phase:** P3 (gated — operator must say "P3 go" before EVE populates this folder).

This folder will hold the `sinister-eve.service` daemon implementation (Rust) + the `eve-overlay` GTK4 prompt + the `eve` CLI client + DBus wrappers.

Layout when populated:

```
eve-control/
├── Cargo.toml                    (workspace)
├── crates/
│   ├── eve-daemon/               (the system service)
│   ├── eve-cli/                  (the `eve` CLI)
│   ├── eve-overlay/              (the GTK4 prompt)
│   ├── eve-dbus/                 (DBus surface)
│   ├── eve-sudoers/              (allowlist validator)
│   └── eve-voice-bridge/         (UNIX socket → sinister-voice → text)
├── systemd/
│   ├── sinister-eve.service
│   └── sinister-eve.socket
├── etc/
│   └── eve.toml.example
├── polkit/
│   └── org.sinister.eve.policy
└── README.md                     (this file)
```

Spec lives in `plans/master-plan-2026-05-24.md § 8`.
