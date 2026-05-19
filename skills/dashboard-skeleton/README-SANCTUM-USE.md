# dashboard-skeleton — Sanctum Use

**Canonical Sinister UI source.** This is the design-token + component skeleton every Sinister surface (Sanctum console, panels, agent UIs) consumes.

## Where the real source lives

```
C:\Users\Zonia\Desktop\dashboard-skeleton\
```

This folder (`D:\Sinister Sanctum\skills\dashboard-skeleton\`) is intended to be a **Windows directory junction** (`mklink /J`) pointing at that Desktop path, so the Sanctum agents and tools can consume the same tokens as the product-side designers without copying source.

The operator's current sandbox blocks `mklink`. **Until the junction is established, consume tokens directly from the real Desktop path above.** Treat the Sanctum path as a logical alias; resolve it to the Desktop source at import / build time.

## Key files to consume

Always pull from the real source:

- `tokens/globals.css` — CSS custom properties for the full token set (colors, spacing, radii, shadows, motion).
- `tokens/theme.ts` — TypeScript / JS export of the same tokens for tooling.
- `components/primitives/` — base building blocks (Box, Stack, Text, etc.).
- `components/ui/` — composed UI components (Button, Card, Modal, Table, etc.).
- `components/shared/` — Sinister-flavored shared widgets used across surfaces.
- `docs/THEME-DOCTRINE.md` — the binding rules for color/typography/spacing usage. Read this before adding new components.

## Color doctrine (binding)

The skeleton currently ships a **purple ramp** for back-compat with existing Sinister UIs. This ramp is retained intentionally:

- **Sanctum-specific UIs** (this console, the session launcher chrome, the inventions/tools archive viewer, agent-facing panels inside the Sanctum) **may use the purple ramp** as the accent color:
  - Primary: `#7A3DD4`
  - Soft: `#A06EFF`

- **Panel-side UIs** (operator-facing dashboards, product surfaces, mobile companion) **MUST consume iOS blue** as the accent. See `docs/THEME-DOCTRINE.md` for the full panel-side token set.

If you are unsure which surface a new screen belongs to, default to **panel-side / iOS blue** and ask the orchestrator before flipping to purple.
