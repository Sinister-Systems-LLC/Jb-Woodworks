# source/ — Sinister iMessage Bridge

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Phase:** P1+ (populates when operator connects the farm).

Layout when populated:

```
source/
├── bridge_daemon/             (Python service; polls chat.db, posts to sinister-bus)
│   ├── poll_chat_db.py
│   ├── post_inbound.py
│   └── routes.py              (per-contact rules)
├── send_worker/               (AppleScript wrappers; serial outbound queue)
│   ├── send.applescript
│   └── send.py                (Python wrapper)
├── recv_worker/               (event-driven listener; FSEvents on chat.db)
│   └── tail.py
├── cli/                       (operator-facing CLI: list threads / show recent / send)
│   └── imessage_cli.py
├── tests/
│   ├── test_send.py           (mock-AppleScript)
│   └── test_chat_db.py        (canned chat.db fixture)
├── requirements.txt
└── README.md                  (this file)
```
