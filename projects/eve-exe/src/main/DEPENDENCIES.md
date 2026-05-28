# MX-EVE-UPDATER dependency hints

When MX-EVE-FULL scaffolds `package.json`, the following must be present:

```jsonc
{
  "dependencies": {
    "electron-updater": "^6.3.9"
  },
  "devDependencies": {
    "electron-builder": "^24.13.3",
    "tsx": "^4.19.0"
  },
  "build": {
    "publish": [
      {
        "provider": "generic",
        "url": "http://sinister-vault.local:5078/releases/eve-exe/"
      }
    ]
  }
}
```

`electron-updater` is NOT installed in this lane (no `package.json` exists
yet). `src/main/updater.ts` lazy-requires it so importing the module is safe
before `npm install` runs.

DO NOT remove any `build.*` keys added by MX-EVE-ICON-BORDERLESS; both lanes
only ADD keys per the coordination contract.
