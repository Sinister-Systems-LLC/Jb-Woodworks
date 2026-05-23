# Sinister Freeze :: Compliance Posture + Enforcement Map

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Source:** `_shared-memory/plans/sinister-freeze-2026-05-21/deep-research.md` §8
> **Status:** ✅ enforcement design locked; bridge-layer code lands during PH1

## Why this exists

Joe sells $200K+ Ferraris. Operating in his channels (Gmail, IG DMs, FB Marketplace, eventually SMS) means touching **TCPA, CAN-SPAM, Meta Graph API ToS, Ferrari Group brand-control standards, Florida privacy law, and dealership IT policy** in the same week. One bad automated send = lawsuit / IG account ban / Ferrari dealer-network sanction.

**Enforcement principle:** Every send-eligible feature passes through a bridge-layer guard. Guards are code, not policy. Code refuses; we don't ship a feature that *could* violate.

## Risk matrix

| Risk | Source | Trigger | Bridge-layer guard |
|---|---|---|---|
| TCPA SMS violation | TCPA + 2025 FCC rulemaking [14] | Auto-SMS to a number that didn't double-opt-in | `freeze/comms/sms.py` refuses to send unless `consent.sms_optin_at` is set + checksum matches + sent_count_24h < cap |
| TCPA auto-call violation | Same | Twilio voice call w/o consent | `freeze/comms/voice.py` refuses unless `consent.voice_optin_at` set |
| CAN-SPAM footer missing | CAN-SPAM Act | Email lacks unsubscribe / physical address | `freeze/comms/email.py` injects footer always; refuses Joe-edit that strips it |
| CAN-SPAM deceptive header | Same | From-name doesn't match Joe's identity | `freeze/comms/email.py` locks From: to Joe's-actual-mailbox; rejects spoofs |
| Meta 24h messaging window | Meta Graph policy [15] | DM reply >24h after last user message | `freeze/comms/ig.py` + `freeze/comms/fbm.py` check `last_user_msg_ts`; if >24h, downgrade to "tag" reply (allowed for narrow use cases) or surface to Joe for manual |
| Meta DM rate cap | Same | >200 DMs/hr per IG account | Bridge-layer queue with token-bucket rate limiter at 180/hr (safety margin) |
| IG/TT automation policy | Spur / Inrō docs [15] | Mass-DM unsolicited prospects | Frost never initiates an IG DM to a non-contact; only replies to inbound |
| Ferrari brand-control: discount language | Ferrari Code of Conduct [17] | Draft contains "$X off" / "save $Y" | `freeze/voice/redflag.py` scans drafts; flags or refuses |
| Ferrari brand-control: track-illegal imagery | Same | Generated/curated photo shows public-road track behavior | Photo metadata + classifier check; refuse + surface to Joe |
| Ferrari brand-control: corporate IP | Same | Generated copy/imagery uses Ferrari corporate trademarks/logos beyond standard mention | `freeze/voice/redflag.py` flags Ferrari corporate IP terms (Cavallino, Scuderia trademark uses, F1 livery) for Joe review |
| Florida CCPA-adjacent privacy | FL HB 9 / FTC dealership guidance [33] | Customer PII leaves Joe's PC w/o consent | All PII tagged `pii=true` at row creation; export-blocked unless `consent.export_at` is set |
| Florida + state auto-dealer record-keeping | Dealertrack [33] | Sales-related comms not preserved per retention rules | Audit log immutable; 7-year retention on customer-facing comms |
| Dealership IT policy | Ferrari of Winter Park IT (V2 dependency) | Multi-tenant rollout w/o IT signoff | Hard gate at PH4 multi-tenant — operator + Joe + dealership IT sign DPA before turning on |
| Voice clone disclosure (V3 feature #37) | FL + national AI-disclosure trends | AI-voice voicemail sent without disclosure | Bridge inserts mandatory "This is an AI assistant for Joe" preamble; refuses send without |

## Enforcement architecture

```
                      ┌────────────────────────────────┐
                      │  Joe (clicks "Approve & Send") │
                      └───────────────┬────────────────┘
                                      v
                      ┌────────────────────────────────┐
                      │  PWA / Telegram bot front-end  │
                      └───────────────┬────────────────┘
                                      v
              ┌───────────────────────────────────────────┐
              │  FastAPI :5079 — POST /send/<channel>     │
              │   - validates payload schema (Pydantic)   │
              │   - looks up consent record               │
              │   - rate-limits per channel               │
              └───────────────────────┬───────────────────┘
                                      v
              ┌───────────────────────────────────────────┐
              │  freeze/comms/<channel>.py BRIDGE LAYER   │
              │   - applies ALL guards from risk matrix   │
              │   - calls compliance_audit_log()          │
              │   - REFUSES if any guard fails            │
              └───────────────────────┬───────────────────┘
                                      v
              ┌───────────────────────────────────────────┐
              │  External provider                         │
              │   - Gmail SMTP / SendGrid                 │
              │   - Meta Graph (IG/FBM)                   │
              │   - Twilio (SMS — V2)                     │
              └───────────────────────────────────────────┘
```

## Consent records (SQLite schema preview)

```sql
CREATE TABLE consent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER REFERENCES contact(id),
    channel TEXT NOT NULL,  -- 'email', 'sms', 'voice', 'ig_dm', 'fbm', 'tt_dm'
    optin_at TIMESTAMP,     -- NULL = no consent
    optout_at TIMESTAMP,    -- non-NULL overrides optin_at
    source TEXT,            -- 'manual_joe', 'form_signup', 'replied_to_invite'
    proof_blob_id INTEGER REFERENCES proof_blob(id),  -- screenshot / form submission audit trail
    schema_version TEXT DEFAULT 'sinister.freeze-consent.v1',
    _author TEXT DEFAULT 'RKOJ-ELENO :: 2026-05-21'
);

CREATE TABLE compliance_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actor TEXT NOT NULL,                 -- 'frost-auto', 'joe-manual'
    action TEXT NOT NULL,                -- 'draft', 'send_attempt', 'send_success', 'send_refused', 'export'
    channel TEXT,
    contact_id INTEGER REFERENCES contact(id),
    content_hash TEXT,                   -- sha256 of the actual content (no plaintext stored here; lookup via memory bridge)
    guard_results JSON,                  -- which guards passed/failed
    refused_reason TEXT,                 -- if refused
    schema_version TEXT DEFAULT 'sinister.freeze-audit.v1',
    _author TEXT DEFAULT 'RKOJ-ELENO :: 2026-05-21'
);
```

## Joe-facing UX

- **Onboarding wizard** explains each consent type in plain English: "Want Frost to send SMS reminders for test drives? You'll need each customer to text YES back once. (TCPA law.)"
- **Consent badge** on every contact row: green = sms+email+dms / yellow = some / red = none
- **Refused-send notification** when a guard fires: "Couldn't send to Marcus — his last reply was 26h ago, outside IG's 24h window. Want to call him?"

## Operator gates (multi-tenant V2)

Before turning on dealership-wide:
- [ ] Joe + operator + Ferrari of Winter Park IT sign DPA
- [ ] SOC2-light controls inventory (encryption-at-rest, encryption-in-transit, access logs, incident response plan)
- [ ] Ferrari Group brand-language review of Frost's template library
- [ ] FL state attorney-general "no-action letter" or similar review for the SMS automation
- [ ] Cyber-insurance line item for the Hetzner deployment

## Composes with

- `PLAN.md` — every PH1+ feature passes through the bridge-layer guards
- `STACK.md` — `freeze/comms/<channel>.py` modules implement this map
- `PERSONA-FROST.md` — Frost's "draft only by default" is enforced HERE (no draft can become send w/o passing through bridge)
- `FEATURES.md` — every send-eligible feature targets a specific bridge layer
- `_shared-memory/knowledge/sinister-freeze-project-doctrine.md` — JOE-SAFETY 7th contract is the policy this code expresses

## Sources

- [14] TCPA + CAN-SPAM Auto Dealership Compliance 2025 — TradePending / CompliancePoint / ClickPoint
- [15] Instagram DM Automation Rules 2025 — Spur / InstantDM / Inrō
- [17] Ferrari Group Code of Conduct + Dealer Compliance
- [33] Florida + State Auto Dealer Privacy 2025 — Dealertrack / OGC / FTC
