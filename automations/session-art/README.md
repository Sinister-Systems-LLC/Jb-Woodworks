<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Session Art Pool

Random ASCII art pieces shown at the top of the Sinister launcher (`start-sinister-session.ps1` v6.1+). One picked uniformly at random each launch.

## How

`Pick-RandomArt` in the launcher PS1 reads `*.txt` from this folder, picks one, splits into lines, centers each, prints in `$C.LightP` (magenta).

## Adding new pieces

1. Drop a new `.txt` here. Naming: `NN-name.txt` for ordering legibility (NN is informational; selection is random regardless).
2. Keep width <= 50 chars so it centers cleanly in a 100-wide console.
3. Keep height <= 18 lines so the picker block still fits on one screen.
4. Plain ASCII or low-Unicode. No tabs (use spaces). No trailing CRLF that would skew Center alignment.
5. Style: speckle / silhouette using `# @ % * ^ ( ) = . - _` — sinister theme. Match the jcode aesthetic (operator's reference 2026-05-23).

## Current pool

| File | Subject |
|---|---|
| 01-skull.txt | skull face |
| 02-raven.txt | perched raven |
| 03-spider.txt | spider with web |
| 04-octopus.txt | octopus (jcode-pattern reference piece) |
| 05-dragon.txt | dragon head |
| 06-eye.txt | sinister eye |
| 07-sigil.txt | S-sigil with SANCTUM tag |
| 08-wolf.txt | wolf head |

All Author: RKOJ-ELENO :: 2026-05-23.
