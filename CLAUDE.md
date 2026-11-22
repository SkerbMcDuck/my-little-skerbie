# My Little Skerbie

A Tamagotchi-style monster-raising game for George's jailbroken iPhone X, played offline. Built with Phaser 3 + TypeScript + Vite and wrapped with Capacitor.

## Read first
- `HANDOFF.md`: where the project stands and what to do next.
- `BUILD_SPEC.md`: the game, final for v1. Build exactly this; numbers marked *tunable* go in `src/config/balance.ts`.
- `ART_BRIEF.md`: every visual asset, with sizes, frames, palette and dye zones.
- `docs/history/`: the raw Q&A logs the spec came from. Use them only to understand *why* a decision was made; the spec wins if they conflict.

## Rules
- **Security first.** The game makes no network calls and has no accounts, analytics or ads. No secrets in the repo (it's public). Pin GitHub Action versions. Keep dependencies minimal. Read any third-party code before adding it.
- **Never call the game "pocket monster."** The working title is My Little Skerbie.
- **Art:** use the project skill `.claude/skills/pixel-art` and the house style in `ART_BRIEF.md`. Source grids go in `art/source/`, rendered output in `art/out/`. Render with `python tools/render.py <json> --out <dir>`. Always view the render before calling an asset done. Skerbie must stay an original design.
- **Don't change a decided design on your own.** If something in the spec seems wrong or impossible, ask George, and say what you'd do instead.
- **Talk to George in plain words.** He's learning to code, so explain what you did and why, briefly.
