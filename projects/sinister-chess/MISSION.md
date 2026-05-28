# Sinister Chess — Mission

## Why this exists

The operator (and Leo) want to climb in chess as fast as possible. Most chess training is one-size-fits-all: drill the same openings everyone drills, watch the same lectures everyone watches, play random opponents whose ELO mismatches yours. That's slow.

Sinister Chess is built around two assumptions:
1. **Growth happens at your edge** — not at your level, not crushingly above it. Calibrated opposition is irreplaceable.
2. **Coaching is most useful when it's specific** — "you blundered queen-trades twice this session because you weren't tracking your light-square diagonal under time pressure" beats "study tactics."

## What this is NOT

- Not a chess platform (no matchmaking, no leagues, no ladder)
- Not a chess server (no remote opponents)
- Not a teaching course (we don't write lectures)
- Not a cheat detector
- Not a database explorer (use lichess for that)

## What it IS

An always-on, always-calibrated, always-honest **personal mirror** that:
- Plays you at exactly the level you'd benefit from
- Watches every move you make, tracks every blunder, every time-pressure mistake
- Tells you — once per session — the 3 most-actionable drills based on YOUR data, not generic advice
- Knows the difference between you and Leo and plays both of you correctly

## How "mirror" works (the model)

A per-player profile that captures:
- **Opening repertoire** — what you actually play (not what you say you play)
- **Time-pressure curve** — at what move count + clock remaining does your blunder rate climb
- **Pattern blind spots** — which tactical motifs you miss vs. find
- **Endgame strength** — K+P vs K rate, R-endgame rate, etc.
- **Stylistic preferences** — aggressive vs positional, sac frequency
- **Recent trajectory** — what's getting better, what's plateaued

The mirror model is used two ways:
1. To pick the right opponent level for THIS session
2. To play AS you (the "vs your mirror at +100 ELO" mode — face a slightly stronger version of yourself)

## Pace promise

The operator wants the **fastest** path to next ELO bracket. Sinister Chess's coaching report each session includes a projection: "at your current improvement velocity, you reach 1500 in ~12 weeks. If you replace your current opening with X, projected to 8 weeks."

Honest projections. Backed by your actual data.

## Privacy

Operator's vault and Leo's vault never cross. Each player's game data, profile, and coaching notes are siloed in `_vault/sinister-chess/<player-id>/`. No leakage.
