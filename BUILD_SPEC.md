# My Little Skerbie: Build Spec (v1)

Hand this to Claude Code. Every decision here is final for v1. Where a number says *tunable*, put it in `src/config/balance.ts` so it can be adjusted without touching game logic. The companion document `ART_BRIEF.md` defines every visual asset, size and animation. Build against it.

---

## 0. What this is

A Tamagotchi-style monster-raising game. You raise one Skerbie, a small, dark, smoky psychic critter, from an egg into a warrior. **You train him by playing short mini-games, and your own skill shapes who he becomes.** While you're away he takes care of himself, gathers, builds his home, explores, and fights off raids. Nothing you earn is ever lost.

Core feel: dark-but-cozy lo-fi fantasy. Short sessions, coming back to see what he did, and a pet that reflects how *you* play.

Design principles (apply them everywhere):
1. **No regression.** Nothing is ever taken away. Bad outcomes only pause progress.
2. **Type changes style, not power.** All three types can do everything equally well. Overall level sets power.
3. **Secretly educational.** Every game trains a real skill. It is never labeled or advertised.
4. **Tap the world.** Actions happen by tapping objects in the scene, not menus.
5. **Security and privacy first.** The game makes no network calls and has no accounts, analytics or ads. All data stays on the device.

---

## 1. Platform and tech

- **Primary device:** a jailbroken iPhone X, iOS 16.7.8, **offline** (no data plan). **Portrait**, 375×812 pt.
- **Test device:** the owner's iPhone 17, in Safari via the web build (never sideloaded), plus a desktop browser.
- **Stack:** TypeScript + Vite + **Phaser 3** (pixel-art mode: `pixelArt: true`, `roundPixels: true`, no smoothing). Wrapped with **Capacitor** for iOS. Use a Capacitor major version whose minimum iOS is ≤ 16.
- **Canvas:** logical **225×487**, scaled exactly **5×** (1125×2436). Integer scaling only. Letterbox with the scene's background color if the aspect ratio differs. **Jungle Run** uses a landscape **487×225** canvas: on entering it, show a small "rotate your phone" icon, and play once the phone is rotated.
- **Orientation:** portrait-locked everywhere except Jungle Run.
- **Capacitor plugins:** Haptics, Preferences or Filesystem (saves), Share (backup export), Local Notifications (installed but unused in v1). No other plugins.
- **Audio session (iOS):** category **ambient / mix with others**, so the player's own music (Spotify, Apple Music, local files) keeps playing. Detect other audio playing (`AVAudioSession.isOtherAudioPlaying`, via a tiny native bridge) and **auto-mute the built-in music** while it's on. Sound effects always mix on top.
- **Haptics:** a single `feel(type)` function (`light`, `medium`, `heavy`, `success`, `warning`). It uses Capacitor Haptics in the app and does nothing on the web. Call it at every "feel" moment (hits, parries, perfects, evolutions, coin pops, hatch).

### Repo and builds
- Public GitHub repo **`SkerbMcDuck/my-little-skerbie`**. No secrets, tokens or keys anywhere in it.
- **GitHub Actions**, pinned action versions:
  - **Web:** build, then deploy to **GitHub Pages** on every push to `main`. The web build includes the **Test panel** (see §14).
  - **iOS:** on a macOS runner, run `npx cap sync ios`, then `xcodebuild` with `CODE_SIGNING_ALLOWED=NO`. Package the `.app` into `Payload/` and zip it as an **unsigned `.ipa`**, fakesigned with `ldid -S`. Upload it as a workflow artifact. It's installed on the X with **AppSync Unified**. The iOS build **excludes the Test panel** (via a build flag).
- **Content Security Policy:** `default-src 'self'`. No remote scripts, fonts, images or fetches. All assets are bundled.
- Keep dependencies minimal and lockfile committed.

---

## 2. Core numbers (tunable defaults)

| Thing | Default |
|---|---|
| Training session | 3 games, about 30 s each |
| Sessions before worn out | 3 |
| Away-progress value of 1 session | ≈ 2 h of away progress |
| Away-progress accumulation cap | 24 h |
| Self-care cap | 80% (player care always adds more) |
| Kid evolution | right after the first training session |
| Adult evolution (form locks) | level 15 (about 2 weeks of regular play) |
| Max level | 50 (about 2–3 months) |
| Subtype ranks | 10 each × 9 = 90 points |
| Skill points earned | 1 per session + 1 per level-up (all maxed ≈ level 40) |
| Raids | max 1 per day, only while the app is closed |
| Chest | 20 slots (upgradable) |
| Overflow pile | last 10 items, held 24 h, then auto-scrapped into materials |
| Type specialty edge | ≤ 10% |
| Adaptive content target | ≈ 75% player success rate |

---

## 3. The Skerbie

- **One Skerbie per save in v1.** The save format supports multiple Skerbies (an array) for the later team feature.
- **Name:** chosen at hatch. Default "Skerbie", max 12 characters, editable later in Settings.
- **Stages and forms (8 total):** Egg → Baby (1 form) → Kid (3 forms: Speed, Strength, Mind) → Adult (4 forms: Speed / Strength / Mind / Balanced).
- **Body plan:** baby = four-legged; kid = crouched and half-upright; adult = upright humanoid.
- **Kid form follows the lead:** the kid form always matches whichever type currently has the most type XP. When another type takes the lead, play a **mini evolution** (a short smoke flash) and switch. Ties keep the current form.
- **Adult form locks at level 15:** it's the type with the most type XP at that moment, **or Balanced** if the top type's XP is less than 10% above the second type's (tunable). Permanent.
- **Evolutions** (egg → baby, baby → kid, kid → adult) use the big shared evolution sequence (a white silhouette, a light pillar and smoke, then a burst reveal). Kid-form switches use the mini version.
- **Colors (dyes):** see §11. Colors carry through every evolution. The egg always looks the default.

---

## 4. Progression: XP, types, levels, skill points

- **3 main types:** Speed, Strength, Mind. Each has **3 subtypes** (below).
- **A training session** = 3 games in a row: **one random game from each type's pool**. The score in each game becomes **type XP for that type** and **overall XP**.
  - XP gained = `score × difficultyMultiplier` (tunable). More play = more XP. There are no personal bests.
- **Overall level** comes from total overall XP. The curve is tuned so adult ≈ 2 weeks and level 50 ≈ 2–3 months of regular daily play (assume ~3–6 sessions/day).
- **Skill points:** +1 per completed session, +1 per level-up. They're spent freely on subtypes in the **Stats panel** (hold on Skerbie). **No respec:** everything is maxable, so no build can go bad.
- **Subtypes** (10 ranks each; each rank is a small permanent boost; all useful to every type):
  - **Speed:** *Reflex* (acts first more often in fights), *Agility* (dodge chance), *Hustle* (faster exploring while away).
  - **Strength:** *Power* (damage), *Toughness* (damage taken ↓), *Stamina* (lasts longer in raids; needs less food).
  - **Mind:** *Alchemy* (better crafted items and potions), *Arcana* (stronger magic; small boost to any type's specials), *Tactics* (smarter auto item use; faster move charge in the Delve).
- **Type changes style, not power:** a Skerbie's fighting power, raid survival, exploring, gathering and crafting all scale with **overall level and subtypes**, never with which type leads. The type only changes *how* he does things (animations, move list) and gives at most a **10% specialty edge**: Speed explores a bit faster, Strength gathers a bit more, Mind crafts a bit better. **Raids must be tuned so all types at the same level survive about the same number of waves.**

---

## 5. Moves and the chalkboard

- **No "teach" action in v1.** Moves **unlock automatically** at set levels, with a "he figured out a new move!" moment (the move's effect plays, plus a short banner).
- **Move lists:**
  - **Shared basics** (every type): Tackle, Guard, and 1 more at a mid level.
  - **Mind (magic):** purple spells, potion brewing mid-fight, traps, reading enemy patterns (for example: Hex Bolt, Brew Tonic, Rune Trap, Foresight).
  - **Strength (power techniques):** for example Ground Slam, Iron Stance, Shrug Off, Haymaker.
  - **Speed (tricks):** for example Flurry, Sidestep, Pickpocket (steals an enemy item), Shadow Dash.
  - About 6 moves per type list across levels 2–40 (exact list and unlock levels tunable; balance each list equally).
- He gets **his first signature move when he becomes a kid**.
- **If the kid form switches type,** he keeps every move he learned. He only learns new moves from the *currently leading* type's list.
- **The chalkboard** (in the den) is where you pick his **4-move fight loadout** from everything he's learned. Later it becomes Spellbook's study spot.

---

## 6. Needs, feeding, energy and self-care

- **Needs:** **Hunger** and **Energy**. Both drift down in real time on an **ease-out curve**: fast at first, then slowing (George's call: daily urgency without frustration). Defaults (tunable): full → half in about 3 h, half → low in about 6 h more, low → empty in about 15 h more. Overnight sleep (22:00–07:00 local) slows the drift to ¼.
- **Needs never cause loss.** They only set his **work rate** while you're away (see §8): well-fed and rested = full rate; hungry or tired = he naps and progress slows; empty = progress pauses.
- **Self-care:** he feeds himself from the pantry, rests, and keeps clean on his own. His self-care effectiveness scales with **overall level** (never with type), up to an **80% cap**. Player care always beats self-care.
- **Training energy:** each session tires him. After **3 sessions he's worn out and can't train or delve again until you feed him** (this only applies while you're playing).
- **Feeding (tap the pantry or food bowl):** a meal from you fully refills Hunger and Energy and gives a small boost (tunable). It uses 1 food from the pantry.
- **Pantry:** stocked by what he gathers while you're away and by the garden. **If it's empty, you can always give 1 free snack** (enough for 1 more training round).
- **Foraging (tap the root door):** a relaxed ~30 s mini-game in a misty forest clearing. Fruit, berries and mushrooms fall from a twisted tree, and he runs side to side catching them, avoiding the rotten ones. It **earns food, not XP**: about 1 training round's worth per forage.
- **Garden** (a buildable on the surface): grows food passively through growth stages (sprout → growing → ripe). Tap ripe plants to harvest. Garden ingredients can also be sold.

---

## 7. The home scene

- **Portrait cutaway side view** of a den under the roots of a huge ancient tree:
  - **Top ~30% surface:** forest floor, a time-of-day sky, the root **door** (foraging), the **garden**, the **merchant cart** (when visiting), and the **overflow pile**.
  - **Middle ~50% den:** hearth, lanterns, bed, **pantry**, **training spot**, **chalkboard**, **blueprint board**, **chest**, **workbench**, **radio** (audio toggles), and his trophies and decor.
  - **Bottom ~20% deep roots:** at the kid stage, **a crack opens in the floor = the Cave Delve entrance**.
- **Interactions (tap the world):**
  - Tap **Skerbie** to pet him (reaction + `feel('light')`). After a KO, the tap **patches him up** instead.
  - Hold on **Skerbie** for the **Stats panel** (level, type XP bars, subtypes, skill points, loadout summary).
  - Pantry or bowl: feed. Training spot: start a session. Door: forage. Crack: Cave Delve. Chalkboard: move loadout. Blueprint board: choose his next build. Chest: inventory and gear. Workbench: crafting. Merchant cart: shop. Overflow pile: reclaim items. Radio: sound and music toggles. Garden plants: harvest.
  - A small **settings gear icon** in a corner opens Settings.
- **Discoverability:** anything new or relevant gets a small **bounce or sparkle** (shared effect) until it's first tapped.
- **Time of day:** follows the phone's real clock: Dawn 6–9, Day 9–17, Dusk 17–20, Night 20–6, blended smoothly. Ambient weather: occasional night rain, drifting leaves by day (visual only).
- **Den tiers:** Burrow → Hideout → Lair. Each tier upgrade is a **blueprint-board build** that unlocks at **level 8 (Hideout)** and **level 25 (Lair)** (tunable) and costs materials. Every buildable shows in the current tier's art style.

---

## 8. While you're away

- On return, compute elapsed time since the last save (**capped at 24 h**). Simulate his loop over that time at his **work rate** (from needs, level and Hustle):
  - **Gathering:** food for the pantry and **materials** (wood, stone, scrap).
  - **Building:** works on the current blueprint (his own pick, or the player's choice from the blueprint board). Progress shows as a shared **scaffolding** overlay until done.
  - **Exploring:** finds items (consumables, gear, materials, ingredients).
  - **Resting:** when tired or hungry, which slows the above.
- **Clock safety:** forward jumps are limited by the 24 h cap. If the clock goes backward, ignore the gap (no gain, no punishment).
- **"While you were gone" recap:** a single **journal-page card** on return, tapped through in seconds. It lists what he gathered, built, found, the raid report (if any), and any items that went to the overflow pile.

### Raids
- **At most 1 per day**, at a random time, **only while the app is closed.** No notifications.
- Enemies come in **waves of rising difficulty**, matched to his **stage** (Gloomlings for a baby, Thornbacks for a kid, the Hollow for an adult). The final wave includes the family **boss**.
- He fights automatically with the shared battle engine (§10), using his loadout and auto-using consumables. **He's always meant to lose eventually.** His level, subtypes and gear decide how many waves he lasts.
- **Rewards:** XP and loot for every enemy defeated before he fell.
- **Aftermath:** he's **knocked out**, and away progress **pauses** until you **tap him to patch him up** (one tap). **Home damage** shows as the shared damage overlays on a few buildables. They repair over time on their own, or instantly by spending materials (tap the damaged item). **Nothing is ever destroyed or lost.** Walls and traps (buildable) make him last longer.
- The raid report appears in the recap.

---

## 9. Training games (v1: 6 games, 2 per type)

Every game: about 30 seconds (Block Party 30–40 s), shows a **3-second animated how-to the first time** (no text tutorials), uses form-appropriate animations (baby / kid / adult, see ART_BRIEF), and scores 0–100 (normalized, tunable).

**Two difficulty dials in every game:**
- **Pressure** (speed, timers, enemy count, surges) scales with **his** related stats and level.
- **Content difficulty** (word length, math complexity, puzzle size) **adapts to the player**, targeting about 75% success, based on their recent results in that game.
- The baby stage is forgiving.

### Speed
1. **Word Rush** (typing). A cliff path at dusk. Enemies from his current stage family charge in from the right, each carrying a **word on a wooden sign**. Typing the word knocks that enemy back. Play happens in the **top half** (the keyboard covers the bottom). Use a hidden input with **autocorrect, autocapitalize and spellcheck off**. Letters light up amber as they're typed correctly. A typo flashes red, and you keep going. Words are game-themed (monsters, items, moves) and get longer and more numerous as the player improves. Speed stat raises the charge speed. Score = words cleared + accuracy.
2. **Jungle Run** (dexterity, **landscape**). An auto-running side-scroller: **tap to jump, hold to swing** from glowing vine anchors. Obstacles: logs, gaps, root snares, low branches, critters. It speeds up over time. **About every 30 s, a treasure clearing** (a safe break) awards loot. He **keeps running automatically**. A small **home icon** (always visible) ends the run and keeps everything. Loot grows at later clearings. **A fall keeps everything from reached clearings and loses only the current stretch.** Biomes rotate at each clearing (Twilight Jungle → Misty Bog → Overgrown Ruins → Moonlit Canopy → darker loop). Ground is tile-based and generated endlessly. Score = distance + clearings reached.

### Strength
3. **Block Party** (rhythm). He stands in the center of a stone arena. Enemies march in from **4 directions on a beat**. Each one has an **element** (color-coded): Ice, Fire, Water or Lightning. Tap the **counter element pad** as the enemy reaches its hit ring, and he swings his **elemental hammer**:
   - Counter chain: **Ice → Fire, Fire → Water, Water → Lightning, Lightning → Earth.**
   - Controls: **4 small element pads in a diamond in the bottom-third thumb zone.**
   - Timing grades: Perfect / Great / Good / Miss. Perfects chain into combos. A miss means he takes the hit and flinches, and the song continues. The element effect shows on the enemy, or on the ground on a miss.
   - Early on, each direction keeps a fixed element. Later, elements mix across directions. Higher Strength means faster songs, more enemies, and doubles (tap two pads at once).
   - A round is one 30–40 s song, with charts tied to the BPM. Score = grade total + combo.
4. **Bar Brawl** (timing and parries). A 1v1 on the tavern floor against a **summoned beast**. The beast **telegraphs** each attack (windup + eye flash):
   - **Tap as it strikes to parry.** A **perfect parry** staggers it and opens a **counter window**, where timed taps land a combo. Clean timing chains bigger hits, and mistimed taps whiff.
   - **Feints and variable timing**, not a beat. The beast escalates with his Strength: Bramble Boar → Frost Yeti → Thunder Ox → Moss Golem → Ember Wyrm.
   - KO it before ~30 s. Tap anywhere in the play area (with nothing else tappable on screen).
   - Score = perfect parries + combo damage + speed. **Winning pays coins** (the main coin source).

### Mind
5. **Potion Brew** (mental math). A cauldron shows a **target number**. Below it is a shelf of **6 numbered ingredients**. Tap them to add, and the total updates live. An **exact hit** bubbles over and scores, and the next potion starts. **Overshooting fizzles** and resets that potion. **Tapping the cauldron dumps the whole potion** (there's no single undo). Brew as many as possible in 30 s. The math adapts to the player: small adds → bigger numbers → subtracting "cursed" ingredients → multipliers (for example "×2 dragon scale") → multi-step. Higher Mind only shortens the timer. Score = potions brewed + low waste.
6. **Rune Lock** (logic). A grid of rune tiles (starting 3×3), each carrying a piece of a glowing line. **Tap to rotate.** Connect the flow from the source rune to the seal. The seal bursts, and a new grid slides in. As many seals as possible in 30 s, with fewer wasted rotations scoring higher. Adapts to the player: 4×4 and 5×5 grids, decoy dead ends, branches feeding 2 seals, locked tiles. **Puzzles are generated on the fly and must be verified solvable.** **Opt-in hints:** after about 8 s without progress, a small hint icon appears. Tapping it makes one wrong tile shimmer and costs points. Ignoring it costs nothing. Higher Mind only shortens the timer.

### Silent skill tracking
Record per-game player metrics locally, **never shown and never mentioned anywhere**: typing WPM and accuracy, math accuracy and response time by operation type, puzzle solve time by grid size, parry timing error (ms), rhythm timing error (ms), Jungle Run reaction stats. Keep rolling history (for example the last 200 results per game). It's used now only for adaptive content difficulty; future achievements will read it.

---

## 10. Battle engine (shared)

One engine for **raids** (fully automatic) and the **Cave Delve** (semi-automatic). Later it'll be used for multiplayer, so keep it deterministic: a seeded RNG, pure functions over plain data.

- Fighters: Skerbie vs 1+ enemies, side view (Skerbie left, enemies right). Stats are derived from level, subtypes and gear.
- Auto-attacks on a timer, influenced by Reflex. Dodges from Agility. Damage from Power, damage taken reduced by Toughness.
- **Moves** (4-move loadout) **charge over time** (faster with Tactics). In raids, he fires them automatically. **In the Delve, the player taps a charged move or item to fire it.**
- **Consumables:** he uses them automatically in raids (smarter with Tactics). In the Delve, the player chooses.
- Enemies by stage family, with 3 roles (grunt, skirmisher, brute) + a boss, and elemental variants.

---

## 11. Items, gear, coins, merchant, dyes

- **Gear slots:** weapon, armor, charm. Each piece has stat boosts. Weapons and armor show on his body as overlays (kid and adult only). Charms show as a small icon.
- **v1 gear:** 6 weapons (bone club, twin knives, spear, hooked blade, rune staff, obsidian greatsword) and 6 armors (leaf wrap, leather vest, scrap plate, chain cowl, bone armor, shadow-iron plate), plus ~6 charms (fang, feather, eye stone, …).
- **Consumables:** health potion, power tonic, bomb, smoke bomb, snack. **Materials:** wood, stone, scrap. **Ingredients:** glowcap mushroom, ember pepper, moonberry, frostmint, ironroot, shadow plum.
- **Rarity:** common, rare, epic. **Sources:** exploring, raid and Delve rewards, Jungle Run clearings, workbench crafting, the merchant.
- **Chest:** 20 slots to start, more via chest upgrades. Hold an item to see its info. Unwanted gear can be **scrapped** into scrap material.
- **Overflow pile:** when the chest is full, new finds go to a pile by the door (last 10 items, 24 h). Tap to reclaim. Leftovers auto-scrap into materials.
- **Workbench crafting:** recipes from materials and ingredients → consumables and gear (better with Alchemy).
- **Coins:** earned from **Bar Brawl wins** (main source), plus raids, the Delve, and selling items or ingredients. **No real money, ever:** no in-app purchases, no ads.
- **Merchant:** a cloaked fox with a lantern cart. He **visits once a day** at a random time while you're playing or away, and stays about 6 h (tunable). Tap the cart to shop: food, materials, ingredients (buy and sell), consumables, occasional rare gear, home decor, and dye packs.
- **Dyes:** recolor Skerbie **anytime, for free**, from the baby stage on.
  - **Zones:** main fur, accent fur, eye glow (always available), and **smoke** (unlocked by a dye pack).
  - **Picker:** a full color wheel **plus hex code entry**. Save colors as **swatches**.
  - **The game generates a 4-shade ramp** (highlight, base, shadow, deep shadow) from the chosen color and swaps it into the zone's reserved palette slots (see ART_BRIEF §Dye zones). Do this with a palette-swap shader or a pre-tinted texture cache.
  - **Dye packs** (coins) unlock **finishes** (metallic, glow, two-tone/gradient, sparkle), extra swatch slots, and the smoke zone.
- ~~Cosmetic hats~~: cut (George, 2026-11-22).
- **Charm auras:** an equipped charm wraps Skerbie in its element's aura (kid and adult stages): ember shard = fire, moon coin = ice, feather = lightning, bone die = earth, fang = water, eye stone = Mind. See ART_BRIEF §5. (George, 2026-11-22.)

---

## 12. Cave Delve

- **Unlocks at the kid stage** (the floor crack). Costs **1 meal of energy** (counts toward worn-out like a session).
- **Floors:** each floor is one fight (30–60 s) in a chamber, with a stairs transition between floors. **A treasure room every few floors** (tunable: every 3rd). Zones: Root Hollows (1–5), Crystal Caverns (6–10), Sunken Ruins (11–15), Hollow Deep (16+, looping darker). **The last floor of each zone is a boss chamber** (the family boss).
- **Semi-auto fights:** he fights on his own, and the player taps charged moves and items.
- **Leave between any floors** and keep everything. **A knockout ends the run, but all loot earned so far is kept.** A KO needs the one-tap patch-up before he can train or delve again.
- Every run starts at floor 1. Already-cleared floors resolve faster (auto-sped). **Best depth** is recorded and shown at the crack.
- Typical run: 3–5 minutes.

---

## 13. First launch (about 5 minutes)

1. An egg sits in the empty Burrow den, wobbling. **Tap it a few times** to crack it (`feel` on each tap).
2. Hatch sequence → **naming** (default "Skerbie", max 12 characters).
3. The **training spot sparkles** → the first session (3 games, each with its 3-second how-to).
4. **Kid evolution** right after, based on the session's results (the kid form follows the lead from then on).
5. Den objects **sparkle once** as they become relevant (pantry, door, chalkboard, crack, and so on). There are no text tutorials.

---

## 14. Settings, saves and the Test panel

- **Settings** (gear icon): sound on/off, music on/off (also on the radio), rename, dye studio shortcut, **Back up Skerbie**, **Restore Skerbie**, backup reminder on/off.
- **Saves:** autosave on every meaningful change and on app background. Keep **3 rolling internal saves**. If the latest is corrupted, silently load the newest valid one.
- **Backup:** "Back up Skerbie" exports the save as a `.skerbie` file through the share sheet (AirDrop to the 17 or the PC). "Restore Skerbie" imports one. Files carry a **version number and a SHA-256 integrity hash**. Reject corrupted or edited files with a friendly message, and never crash on bad input (validate every field). An **in-app** weekly backup reminder (not a notification), which can be switched off.
- **Save format:** versioned JSON with migrations. Stored via Capacitor Preferences or Filesystem in the app, and localStorage (in try/catch) on the web. The web saves (iPhone 17 testing) are separate from the X's.
- **Test panel (web build only, inside Settings, clearly labeled):** skip time (+1 h / +6 h / +24 h), trigger a raid now, fill the pantry, add coins and materials, jump to the next stage, set level, reset save. **Compiled out of the iOS build.**

---

## 15. Audio

- **Built-in music:** a default **free lo-fi** soundtrack (only tracks whose license allows commercial use). It **auto-mutes when the player's own music is playing**.
- **Sound effects:** generated with **jsfxr** (blips, hits, coins, power-ups) plus **CC0** packs for organic sounds (wood creaks, crowd cheers, cauldron bubbles, rain, whooshes). **His voice:** short made-up chirps and grumbles, pitched by stage (squeaky baby → gravelly adult).
- **Block Party** needs its own beat-matched tracks (lo-fi or chiptune-flavored, with known BPM and commercial license).
- **`CREDITS.md`** lists every audio and font asset with its source and license.

---

## 16. Milestones (each must run on the X before the next starts)

**Prerequisite:** the art from `ART_BRIEF.md` (George wants the real art in before the build).

1. **Core loop:** project setup, CI (web + IPA), save system (rolling + backup/restore), the home scene (Burrow, tap interactions, time-of-day lighting), egg/hatch/naming, feeding/pantry/snack/foraging, needs, **all 6 training games** with adaptive difficulty, type XP, levels, skill points + subtypes + Stats panel, kid evolution with lead-switching, audio (music auto-mute, sound effects, radio), haptics, silent tracking, Settings, the web Test panel.
2. **Away loop:** away simulation (24 h cap, work rate, self-care), gathering, building, blueprint board, den tiers, garden, recap card, **battle engine + raids** + patch-up + damage overlays, items/gear/chest/overflow/scrapping, workbench crafting, coins, merchant, dyes + dye packs, charm auras.
3. **Delve and adult:** move lists + auto-unlocks + chalkboard loadout, Cave Delve (zones, treasure, bosses, best depth), adult evolution and lock, level 50 cap, balance tuning pass.

**v1 is done** when all three milestones run on the iPhone X, installed from the GitHub-built IPA.

---

## 17. Not in v1 (planned later)

- **Spellbook** (a trivia Mind game; first to return, studied at the chalkboard to unlock bonus moves). It needs an original, fact-checked question bank.
- **Whack-a-mole** (Speed) and **Club Swing** (golf-style Strength game).
- **Teams:** more Skerbie eggs found at milestones (around levels 15/25/40/50), including **dark animal-humanoid species** (gorilla, croc, falcon, rabbit, elephant, …), each with its own type aptitude.
- **Multiplayer** (after the App Store): fights against friends' Skerbies, and co-op vs hordes.
- **Secret achievements** built from the silent skill tracking.
- **In-game Spotify panel** (needs internet and login).
- **The tavern as a visitable place;** gear dyeing; hybrid forms; more forms and games.
