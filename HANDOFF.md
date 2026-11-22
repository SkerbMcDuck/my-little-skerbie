# Handoff: My Little Skerbie

_Last updated 2026-11-21, after George approved the baby look._

## Where things stand
- **Design is finished.** It was planned over two long Q&A sessions with George (one for the game, one for the art). Every v1 decision is in `BUILD_SPEC.md` (game) and `ART_BRIEF.md` (art). There are no open questions.
- **Art pipeline is set up:** the project skill `.claude/skills/pixel-art` (house style built in), the renderer `tools/render.py`, and a generator example `tools/build_baby.py`.
- **Baby look approved (2026-11-21):** baby Skerbie idle [4] + blink [2] at `art/out/skerbie/` (`baby_skerbie_test.gif`, sheet, frames.json), source grid `art/source/skerbie/baby.json`, built by `tools/build_baby.py`. George asked for it **more angular and aggressive** than the first round version: straight-edged shapes with flat faceted shading, a low pounce-ready crouch, a wedge head with one fang, tall sharp ears, raised accent-fur hackles, narrowed glaring eyes and a spiked stub tail. `ART_BRIEF.md` §4 was updated to match. **This style is locked for everything else.**
- **Baby home animations approved (2026-11-21):** walk [6], happy [4], eat [4], sleep [2], tired [2], petted [3], knocked_out [3] + knocked_out_loop [2], working [4], carry [4], cheer [4], catch [3]. `tools/build_baby.py` makes every frame from one poseable body (bob, crouch, rear, sit, head, feet, ears, tail, eyes, mouth), so idle and blink stay pixel-identical to the approved test. The baby has no tools, so "working" is digging and slamming with a forepaw.
- **Baby fight and game poses drawn (awaiting George's OK):** battle_stance [4], basic_attack [5], signature [6], flinch [2], dodge [3], knockout [4]; run [6], jump [3], vine_swing [4], fall [3]; swing_right/left/up/down [4 each] (headbutt forward, tail-whip back, rear-up headbutt, head slam); brawl_stance [3], parry [3], counter_a [3], counter_b [3], take_hit [2], victory_taunt [3]; guard_stance [3], stirring [3], concentrating [2]. All 37 baby animations are in `art/out/skerbie/baby/`.
- **Baby frame data (`frames.json`):** each frame has a `mouth` attach point (carried loot and the Jungle Run vine grip snap there) and a **`root_dx`**: lunges, dodges and pounces are *not* baked into the 32×32 frame (he'd leave it), so the game must slide the sprite by `root_dx` px on that frame (toward his facing). Vertical hops are baked in.
- The snout tip was 1 px past the frame edge in `eat`; head reach is now capped so nothing clips. That's the only change to an approved animation.
- **Egg approved (SKB-EGG, 2026-11-21):** wobble [3], crack [4], hatch [5] at `art/out/skerbie/egg/`, built by `tools/build_egg.py`. A faceted charcoal shell with red ember cracks; the hatch ends with his ear tips and glaring eyes peeking over the broken rim. Wobble is lean-left / upright / lean-right, so play it back and forth (ping-pong).
- **No game code exists yet.** The repo is empty apart from these docs and art files.

## George's key decisions (quick reference; the spec has the details)
- Offline on a jailbroken **iPhone X** (iOS 16.7.8). Installed as an **unsigned IPA via AppSync**, built by GitHub Actions. Also a **GitHub Pages** web build for testing on his iPhone 17 (which has the Test panel; the IPA doesn't).
- Skerbie: an **original** dark, smoky, red-eyed psychic critter. **Baby = four-legged, kid = in between, adult = humanoid.** 8 forms. The kid form follows whichever type leads; the adult form locks at level 15.
- **6 games:** Word Rush and Jungle Run (Speed, Jungle Run in landscape), Block Party and Bar Brawl (Strength), Potion Brew and Rune Lock (Mind). One random game per type per session.
- **No regression, ever.** Raids happen while he's away and he always loses eventually, but nothing is lost: a one-tap patch-up, and repairable damage.
- **Type changes style, not power.** Mind = purple magic, Strength = power techniques, Speed = tricks.
- **Secretly educational.** Skill tracking is silent and never shown.
- **Free tools only for art** (Claude pixel-art skill). Free lo-fi music that plays alongside the player's own music. jsfxr + CC0 sound effects. No real money, ever.
- **Art first:** George wants the real art made **before** the game build starts.

## What to do next (in order)
1. ~~**Show George the baby test** and adjust it until he approves the look.~~ Done: approved 2026-11-21 (angular and aggressive).
2. **Make the full art order** in `ART_BRIEF.md` with the pixel-art skill. Start with the rest of the Skerbie bodies, then the home, enemies, tavern, game scenes, Jungle Run, the Delve, effects, items and UI. Check in with George after each Skerbie stage.
3. **Build Milestone 1** (core loop), as listed in `BUILD_SPEC.md` §16, including CI for both the web build and the IPA. George tests it on his iPhone 17 (Pages) and on the X (IPA).
4. **Milestone 2** (away loop), then **Milestone 3** (Delve and adult), each one tested on the X before moving on.

## First message to paste into Claude Code
> Read CLAUDE.md, HANDOFF.md, BUILD_SPEC.md and ART_BRIEF.md. Then show me the baby Skerbie test in `art/out/skerbie/` and ask me what to change before you make the rest of the art.

## Notes
- GitHub: `SkerbMcDuck/my-little-skerbie` (public).
- George's PC is Windows (i9-14900F, RTX 5070). There's no Mac, so iOS builds happen only in GitHub Actions.
- Default numbers that weren't explicitly decided (den tier levels 8/25, the Balanced-adult margin of 10%, a Delve treasure room every 3rd floor, merchant visits about 6 h) are marked tunable in the spec.
