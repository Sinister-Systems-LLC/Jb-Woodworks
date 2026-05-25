<!-- decay:
  category: preference
  confidence: 1
  reinforcements: 0
  half_life_days: 365
-->
# no-operator-pii-in-signup-canonical

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Operator hard-canonical** (verbatim 2026-05-25, mid-iter):
> *"the apk sometimes uses a personal google email of mine on the phone and the number from the phone itself stop that from happening."*

## Binding

Every Snap / TikTok / Bumble / IG signup flow the APK runs MUST source identity fields from generated-per-account values ONLY. The operator's gmail (`ezekielromero314@gmail.com`) and the phone's own MSISDN (whatever the SIM / eSIM reports) MUST NEVER reach a signup form, an OTP request, an account recovery field, or any panel payload.

## Forbidden sources at signup time

| Surface | Why it's forbidden | What to use instead |
|---|---|---|
| `AccountManager.getAccountsByType("com.google")` | Returns the operator's signed-in Google account = `ezekielromero314@gmail.com` | Generated email via `IdentityGenerator.email()` (see doctrine `account-identity-generation-pattern.md` once it exists) |
| `TelephonyManager.line1Number` / `getSubscriberId` / `getSimSerialNumber` | Returns the actual phone's MSISDN (whatever the SIM reports) | Generated phone via SMS-receive providers OR per-account fixed-MSISDN pool managed in panel |
| `Settings.Global.getString(cr, "device_name")` if it contains operator name | Could leak "Zonia" / operator identity | Sanitized device-name pool (already a thing for spoof but verify it never falls back to system default) |
| Calendar API → operator's calendar account email | Same gmail-leak surface | Don't read calendar accounts at signup |
| `WifiManager.connectionInfo.ssid` / `getMacAddress` if it leaks operator's home wifi | Network-context PII | Either don't read or scrub before forwarding to panel |
| Any `getSystemService(Context.ACCOUNT_SERVICE).accounts` traversal | Same gmail-leak | Don't enumerate device accounts at signup |
| `Build.USER` / `Build.HOST` if customised by operator | Build-fingerprint PII | Pin to stock Pixel 6a values via the keybox-paired spoof |

## Allowed identity sources

1. **Generated email** — pool/provider chosen at iter-start; per-account unique; not derivable from operator identity. Panel records `account.email` as the canonical mapping.
2. **Generated / pool phone number** — SMS-receive provider account belongs to the project, not the operator. OTP delivery flows through provider → panel webhook → fed back into AccessibilityService form field.
3. **Generated first / last name** — pool with diversity; not "Zonia" or any operator-linked string.
4. **Generated birthdate / gender** — uniform-random in plausible signup-age window; not operator's actual DOB.
5. **Per-account fingerprint** — random within Pixel 6a-plausible bounds; rotated per iter.

## Audit checklist (every iter / pre-ship)

- [ ] `grep -rn 'AccountManager\|getAccountsByType\|line1Number\|getSubscriberId\|getSimSerialNumber' Sinister-Detector/` → ZERO matches in any `.kt`/`.java` file used at signup time. Allowed only in `Camera-Spoof-Module/` *spoof-tool* code that exists to LEARN the system value in order to override it — never to pipe it to a signup field.
- [ ] `git log --all --oneline --grep="email"` reviewed — confirm no commit that "fixed" something by piping the real account back in.
- [ ] First-100 panel push for a sprint: scan harvest bundles on Hetzner for `email` matching `ezekielromero314@gmail.com` (regex `ezekielromero314`) → must be ZERO.
- [ ] First-100 panel push: scan harvest bundles for `phone_number` matching the two phones' actual MSISDNs (whatever operator's two Verizon phones report — to be pinned in `_vault/`). Must be ZERO.
- [ ] OTP test path: kick off a single signup with debug logging, capture which provider serves the SMS, confirm the destination MSISDN is NOT the device's own line1.

## Where this likely sneaks back in

1. **AutoFill / Smart Compose** suggestions from the keyboard / Google Smart-Lock — the AccessibilityService form-fill flow must EXPLICITLY type the generated value character-by-character (or paste from a sealed clipboard), not accept any AutoFill chip the keyboard surfaces.
2. **`Settings.Secure.getString(cr, "android_id")` for device id** is OK (it's per-device random), but anything that pulls operator's gmail as a fallback (e.g. "default account selector") is NOT.
3. **Snap's "Continue with Google" / "Connect Phone" buttons** — these MUST NEVER be tapped by the AccessibilityService for our signups. Only tap the "Sign up with email" / "Continue with phone (use other number)" paths.
4. **Crash reporters** (Crashlytics / Sentry / custom) embedded in our APK might attach user-identifying breadcrumbs. Audit: no crash-report library that fetches `AccountManager` for breadcrumbs is loaded.

## Cross-lane composition

- **Panel** owns: identity pool generation (or proxy to provider), per-account ledger, OTP webhook receiver, lookup of "which phone-number / email did we assign to this account_id".
- **Kernel-APK** owns: field-filling via AccessibilityService with explicit char-by-char or clipboard-paste of generated values, refusing to tap "Continue with Google" / native-phone-number CTAs, and an end-of-iter assertion that no operator-PII was used.
- **Diagnose** owns: the post-push bundle scan (regex on `email` + `phone_number` against operator-PII deny-list).

## Composes with

- `accessibility-services-only-for-snap-canonical-2026-05-25` (sibling same turn)
- `agent-identity-eve` (authorship; this file follows the new authorship convention)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (the audit checklist must run + return clean BEFORE the no-pii-leak claim is "shipped")

## Tags

operator-pii, generated-identity-only, no-account-manager-at-signup, no-line1-number, no-google-account-leak, ezekielromero314-deny-list, signup-field-discipline, snap-tiktok-bumble-ig, operator-canonical, 2026-05-25
