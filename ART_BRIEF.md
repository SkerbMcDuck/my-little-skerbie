# My Little Skerbie: Art Brief (v1)

The complete art order for v1. It's written to be used with the **`pixel-art` skill**: each asset entry is a prompt plus its specs. Prepend **§1 Global style** to every asset prompt. `BUILD_SPEC.md` says how each asset is used in the game.

**Start with the test asset (§16): baby Skerbie idle.** Only produce the full order after George approves it.

---

## 1. Global style (prepend to every prompt)

> Detailed 16-bit pixel art in a late-SNES / modern-indie style. Dark-but-cozy fantasy with a **lo-fi beats** mood: soft contrast; shadows lean dusky purple and deep teal; warm glowing highlights in amber, peach and soft pink, like a desk lamp at 2am. Light comes from the top-left. Characters have dark outlines (selective outlining where the light hits). Backgrounds have soft or no outlines. Clean lines with even steps, no pillow shading, no banding, no orphan pixels. Transparent background. The palette is limited to the §3 colors. Original designs only: never copy or closely resemble an existing character or franchise.

---

## 2. Technical specs

- **Portrait canvas:** 225×487 px (shown at 5× on iPhone X). **Jungle Run canvas:** 487×225 px (landscape).
- **Sizes:** Skerbie baby 32×32, kid 48×48, adult 64×64. Icons 24×24. Tiles 16×16. Other sizes as listed per asset.
- **Colors:** about 12–16 per character, about 32 for the whole world, all from §3.
- **Animation:** 10 fps by default. The feet or base stay on the same row unless the motion is a jump or float. Secondary motion (ears, tail, scarf, smoke) lags 1 frame. Loops must be seamless.
- **Facing:** draw every character facing **right** only; the game flips it.
- **True side view:** only the near eye shows. Don't draw a sliver of the far eye over the snout (George, 2026-11-21).
- **Attachment points:** for every kid and adult body frame, record `head`, `hand` (the weapon grip) and `torso` pixel coordinates in the frame data. Gear and hats snap to these.
- **Effects** (smoke, sparks, elemental hits, sparkles) are **separate sprites**, never baked into bodies. Glowing effects (fire, lightning, magic, eye glow) get an extra **soft-glow layer** (a separate PNG, blended additively).
- **Effect sizes:** combat and element effects in **small** (for babies, kids and small enemies) and **large** (for adults, the Hollow and bosses). UI effects in one size.
- **Delivery per asset:** a 1× PNG sprite sheet (transparent, **one row per animation**), a scaled preview, a GIF per animation, and `frames.json` (animation names, frame counts, fps, attachment points, dye zones). The source JSON grids are kept in the repo.

### Dye zones (word this exactly into every Skerbie body prompt)
Skerbie has **4 dye zones**: (1) **main fur** (default black), (2) **accent fur** (belly, mane, ear tips, markings; default dark grey), (3) **eye glow** (default red), (4) **smoke** (bonus zone, unlocked by a dye pack). Each zone is drawn with its **own reserved set of 4 shades** (highlight, base, shadow, deep shadow) used nowhere else on the sprite. The game generates a matching 4-shade ramp from any chosen hex color and swaps it in, so shading and depth survive any color. **Outlines and gear are never dyed.** All 8 bodies use the same zone slots in consistent positions.

Reserved palette slot characters (use these in every Skerbie grid): main fur `1 2 3 4`, accent fur `5 6 7 8`, eye glow `e E f F`, smoke `s S t T` (each listed highlight → deep shadow). Outline `o`.

---

## 3. Master palette

| Use | Hex (highlight → deep) |
|---|---|
| Outline (characters) | `#0f0d14` |
| **Main fur** (zone 1, default black) | `#4a4552` `#2a2630` `#1a1720` `#0b0a0e` |
| **Accent fur** (zone 2, dark grey) | `#8a8494` `#615b6b` `#433e4c` `#2c2833` |
| **Eye glow** (zone 3, red) | `#ff9a8a` `#ff3d3d` `#b81f2e` `#6e0f1c` |
| **Smoke** (zone 4) | `#7a7088` `#554c63` `#3a3346` `#251f2e` |
| World charcoal | `#33303d` `#23212b` `#17151c` |
| Slate blue | `#4d5e7a` `#3b4a63` `#2a3448` |
| Moss green | `#557a5c` `#3e5a46` `#2c4234` |
| Dusky purple shadow | `#4a3a5c` `#3a2d4a` `#2a2036` |
| Deep teal shadow | `#2c5560` `#1f3d44` |
| Warm light (amber / peach / pink) | `#ffd08a` `#ffb35c` `#ff8a3d` `#ffc8a8` `#f2a0b0` |
| **Mind magic (purple)** | `#e2b8ff` `#c77dff` `#9b4dff` `#6a2cc9` |
| Fire | `#ffe08a` `#ffb347` `#ff7a1a` `#c2410c` |
| Water (teal) | `#8ff0e6` `#2ec4b6` `#178f86` |
| Lightning | `#ffffff` `#fff4b0` `#ffe14d` |
| Earth | `#a8945e` `#8b7a4a` `#5f7a3a` |
| Ice | `#f2f9ff` `#cfe9ff` `#9fc9f0` |
| Enemy eyes (sickly) | `#e4f27a` `#c8e04a` |
| Rarity frames | wood `#7a5636` · silver `#c9cfd6` · gold `#f2c14e` |
| UI | dark wood `#3b2a22` · parchment `#bfae8c` · iron `#5a5e66` |
| Type colors (UI) | Speed silver `#c9cfd6` · Strength bronze `#a8643a` · Mind purple `#9b4dff` |

**Color lanes (never break them):** pure near-black (`#0b0a0e`) is for Skerbie's fur only. **Red** is for his eyes, danger and fire only; on enemies, red appears only as attack-warning flashes. **Bright purple** is Mind magic only (shadow purples stay dusky and muted). Enemy eyes are sickly yellow-green.

---

## 4. Skerbie: an original dark psychic critter

**Character core (include in every Skerbie prompt):**
> Skerbie: an original, small, dark, smoky psychic critter. Black and dark-grey fur, large expressive ears, glowing smoky red eyes, a mischievous but lovable attitude. Wisps of dark smoke curl off him when he's excited, powering up, evolving or moving fast. His eyes glow faintly, brighter in the dark, so he reads even as a silhouette. He's an original design inspired by "lean psychic critter" vibes, and must not resemble any existing creature.

**Body plan:** baby = **four-legged**; kid = **in between** (crouched, half-upright, can rear onto hind legs); adult = **upright humanoid animal**.

| ID | Form | Size | Description |
|---|---|---|---|
| SKB-EGG | Egg | 24×32 | A smooth charcoal-black shell with faint red ember-glow cracks. Smoke wisps leak from the cracks as it nears hatching. |
| SKB-BABY | Baby | 32×32 | A small, **angular and aggressive** **quadruped** in a low, ready-to-pounce crouch: an oversized wedge-shaped head with a long pointed snout and one small fang, tall sharp swept-back ears, a sawtooth ridge of raised hackles (accent zone) along the back, narrowed glaring red eyes and a short spiked stub tail. Small and fierce, a little spooky. (Changed from "round, clumsy, adorable" by George, 2026-11-21.) |
| SKB-KID-SPD | Speed kid | 48×48 | Sleek and lean, crouched half-upright. Swept-back ears, a long thin tail, a tattered scarf that trails behind him. |
| SKB-KID-STR | Strength kid | 48×48 | Stockier, crouched half-upright. A thick grey fur mane on the shoulders (accent zone), wrapped forepaws. |
| SKB-KID-MND | Mind kid | 48×48 | Extra-tall ears with smoky glowing tips, faint rune markings (accent zone). Hovers slightly off the ground. |
| SKB-AD-SPD | **Shadow Stalker** (Speed adult) | 64×64 | Upright, lean and agile. A hooded cowl, a blade-tipped tail, a constant smoke trail. |
| SKB-AD-STR | **Juggernaut** (Strength adult) | 64×64 | Upright and hulking. Scarred grey fur (accent), a heavy grounded stance, massive forearms. |
| SKB-AD-MND | **Occultist** (Mind adult) | 64×64 | Upright, robed and floating. Glowing sigils in his fur (accent), a halo of smoke. |
| SKB-AD-BAL | **Warden** (Balanced adult) | 64×64 | Upright and cloaked, steady and watchful. A balanced mix of the other three. |

**Armor and weapons are not part of any body.** They're gear overlays (§5).

### 4.1 Animations, for every body (frame counts in brackets)

**Home:** idle (breathing + ear twitch) [4], blink [2], walk [6], happy bounce [4], eat [4], sleep with drifting smoke [2], tired slump [2], petted reaction [3], knocked out [3, then a 2-frame loop], working/hammering [4], carrying loot [4], level-up cheer [4], catch (foraging) [3].

**Fights (raids and Delve):** battle stance [4], basic attack [5], signature move [6], flinch [2], dodge [3], knockout [4].

**Games:**
- Jungle Run: run [6], jump [3], vine swing [4], fall [3]
- Block Party: hammer swing up / down / left / right [4 each]
- Bar Brawl: brawl stance [3], parry [3], counter strike A [3], counter strike B [3], take hit [2], victory taunt [3]
- Word Rush: guard stance [3]
- Potion Brew: stirring [3]
- Rune Lock: concentrating [2]

**Body-plan versions of the game poses:**
- **Baby (four-legged):** Block Party = headbutt or tail-whip toward each direction; Bar Brawl = headbutts and pounces; Jungle Run = runs on all fours, pounces over gaps, swings by **mouth or tail**; Potion Brew / Rune Lock / Word Rush = sits, paws and pounces. Baby holds no gear and no hammer (the elemental effect bursts from the headbutt).
- **Kid (in between):** grips a **small** hammer; brawls with small fists and forepaws; scrambles and leaps on the run.
- **Adult (humanoid):** full hammer swings, full bar-fight punches and parries, athletic running and swinging.

**Egg only:** wobble [3], crack [4], hatch [5].

Roughly 35 animations / ~135 frames per body × **8 bodies**.

---

## 5. Gear overlays and hats

- **No visible gear on the baby.**
- **Weapons and armor** are drawn in **2 sizes** (kid 48, adult 64). They snap to the `hand` and `torso` points and must work on every form of that size. The frames follow the body's animations, so each gear piece needs overlay frames matching every body animation that shows it. (Practical rule: draw weapons as a few rotation poses keyed to the grip point; armor as a fitted overlay per body.)
- **Weapons (6):** bone club (common), twin knives (common), spear (rare), hooked blade (rare), rune staff (epic, faint purple glow), obsidian greatsword (epic).
- **Armors (6):** leaf wrap (common), leather vest (common), scrap plate (rare), chain cowl (rare), bone armor (epic), shadow-iron plate (epic).
- **Charms** don't show on the body, only as icons (§13).
- **Cosmetic hats (~6)**, kid and adult only, 2 sizes, on the `head` point. They override an armor headpiece. Ideas: hooded cowl, wizard hat, iron helm, leaf crown, bandana, horned cap.

---

## 6. Home: the root den

**ID: HOME.** Portrait 225×487 cutaway side view of a den hollowed out under the roots of a huge ancient tree at the edge of a dark forest.
- **Top ~30%, the surface:** forest floor, the trunk rising out of frame, a **root door**, a garden patch spot, space for the merchant cart, and the overflow pile spot.
- **Middle ~50%, the den:** root-and-stone walls with fixed spots for each buildable (bed bottom-left, workbench right, and so on).
- **Bottom ~20%, the deep roots:** dark roots and stone, plus **SKB-CRACK**, a floor crack glowing faintly from below (the Cave Delve entrance; it appears at the kid stage), in 2 states: hidden and open.

**Backgrounds** are drawn in **neutral lighting**, once per den tier:
- **Burrow:** a rough dirt hollow, bare roots, one candle.
- **Hideout:** stone-lined walls, root-carved shelves, a rug.
- **Lair:** carved stone pillars, iron fixtures, banners, trophy mounts, rune-lit wall glyphs, an iron-reinforced root door.

**Skies (4, for the surface):** Dawn (cool pinkish-grey with mist), Day (muted overcast, never bright sunny), Dusk (deep orange to purple, long shadows), Night (dark blue, stars).
**Lighting overlays (4):** a color-tint layer plus glow maps for the lanterns and hearth, per phase. The den changes less than the surface. At night his eyes glow brightest.
**Ambient sprites:** rain streaks (loop) [4], door drips [3], drifting leaves [4], fireflies [4], mist wisps [4].

### 6.1 Buildables (each one in Burrow → Hideout → Lair styles)
| ID | Buildable | Burrow → Hideout → Lair |
|---|---|---|
| B-BED | Bed | leaf pile → root hammock → fur-draped stone slab with skull headboard |
| B-PANTRY | Pantry | wall hole with a few berries → plank shelves with jars and hanging herbs → iron-banded larder with smoked meats |
| B-WORK | Workbench | flat rock with stick and stones → pegged wooden bench with tools → anvil and glowing forge corner |
| B-CHEST | Chest | hollow log → wooden trunk → iron-bound chest with a rune lock |
| B-WALLS | Walls and traps | sharpened sticks at the door → palisade and snares → spiked iron gates and rune wards |
| B-TRAIN | Training gear | a lifting rock → dummy and weights → full rack with an enchanted dummy |
| B-HEARTH | Hearth | campfire ring → stone hearth with a pot → carved fireplace with a smoke chimney (animated fire [4]) |
| B-DECOR | Lanterns and decor | candles → hanging lanterns → rune sconces, banners, trophy mounts (flicker [3]) |
| B-GARDEN | Garden (surface) | dug patch → raised beds → glowing mushroom-and-herb grove |
| B-CHALK | Chalkboard | slate leaning on a root → framed board → carved stone tablet |
| B-BLUEPRINT | Blueprint board | bark with scratches → pinned parchment board → iron-framed drafting board |
| B-RADIO | Radio | a hollow gourd with strings → a wooden music box → an ornate rune-lit gramophone |

**Shared overlays:**
- **SCAFFOLD:** wooden frames, rope, a hammer-dust puff [3], drawn over a faded outline of the build in progress. Reused for everything.
- **DAMAGE KIT:** cracks, scorch marks, scattered debris, a lingering smoke wisp [3], a broken plank. They're layered onto damaged buildables and fade piece by piece during repair.

---

## 7. Enemies (raids, Delve, Word Rush)

Every enemy: approach/walk [4], attack windup [2] (**with a red warning flash**), strike [3], hit [2], defeat [4]. Bosses add intro/roar [4] and special attack [6]. **Enemy eyes are sickly yellow-green.** Elemental variants (ice, fire, water, lightning) are **palette swaps**, plus the elemental aura effect.

| Family (stage) | Size | Look | Roles (grunt / skirmisher / brute) | Boss | Defeat effect |
|---|---|---|---|---|---|
| **Gloomlings** (baby) | ~24px | mischievous twig-and-moss imps, more pest than threat | twig imp / leaf darter / mossy lump | Gloom Mother (≈1.5× brute) | bursts into leaves |
| **Thornback bandits** (kid) | ~40px | goblin-ish scavengers in scrap armor, crude clubs and slings | club thug / sling runner / shield brute | Thornback Chief | drops gear and flees |
| **The Hollow** (adult) | 64–80px | tall armored shadow-brutes and wraith beasts from the deep forest, genuinely menacing | hollow knight / wraith hound / hollow colossus | The Hollow King | dissolves into black smoke |

---

## 8. The tavern (Bar Brawl)

- **TAV-BG: The Gnarled Tankard.** A smoky, lantern-lit wooden hall dug into a hill: barrels, a long bar, **an open floor in the middle for the fight**, lo-fi colors. Background **breakables**: chairs and mugs [3-frame smash each].
- **TAV-CROWD:** silhouetted critters around the edges, cheer loop [2], plus an erupting version [2].
- **NPC-BADGER (bartender):** a hulking one-eyed badger in a stained apron. idle [3], slides coins across the bar [4].
- **NPC-DRUID (ringmaster):** hooded, **antlered**, with a gnarled staff. Green runes glow as he summons: idle [3], summon [5] (with a ring-of-light effect).
- **Beasts** (fantastical, distinct from raid enemies; facing right; flipped to face Skerbie):

| ID | Beast | Size |
|---|---|---|
| BST-1 | Bramble Boar | 64 |
| BST-2 | Frost Yeti | 72 |
| BST-3 | Thunder Ox | 80 |
| BST-4 | Moss Golem | 88 |
| BST-5 | Ember Wyrm | 96 |

Beast animations: summon-in [4], idle [3], **windup tell** (eye flash) [3], strike [3], **feint** [3], staggered [3], hit [2], KO and poof back into the druid's light [4].

---

## 9. Game scenes

- **GS-WORD (Word Rush):** a rocky cliff path at dusk. Composed for the **top half** (the keyboard covers the bottom). Skerbie guards on the left, and enemies charge in from the right. **Word sign:** a tattered wooden sign (9-slice, so it stretches to the word length). Typed letters glow amber. A correct word = knockback + a dust puff [3].
- **GS-BLOCK (Block Party):** a round stone arena in a moonlit clearing, 4 faint **hit rings**, and ground that **pulses with the beat** [2]. **Elemental hammer** (kid and adult sizes): a chunky dark-iron maul with a glowing core in 5 element colors. **Thumb pads:** 4 small carved rune stones (fire, water, lightning, earth), each in idle and pressed states, arranged in a diamond in the bottom third.
- **GS-BREW (Potion Brew):** a close-up of his alchemy corner. A bubbling iron cauldron [bubble loop 4], the target number glowing in the steam, and a shelf of **6 ingredient sprites** (mushroom, eye jar, dragon scale, crystal, feather, bone) with carved number tags. **Cursed** ingredients get a sickly green-black aura [3]. **×2** ones get a gold sheen [3]. Success = a colored plume [5]. Fizzle = a grey sputter [4]. Dump = a splash-out [4].
- **GS-RUNE (Rune Lock):** an ancient **stone seal door**. **Tiles:** carved slate with glowing channel pieces (straight, corner, T, cross, dead end), in unlit and **purple-lit** states, plus a locked-tile variant. A **source rune** [pulse 4], a **seal glyph**, the seal bursting in smoke [6], and a hint shimmer [3].
- **GS-FORAGE (Foraging):** a misty forest clearing with an old twisted fruit tree. **6 foods** (fruit, berries, mushrooms) + **1 rotten** (dark, wrinkled, flies), each with a 2-frame tumble.

---

## 10. Jungle Run (landscape 487×225)

- **4 parallax layers** per biome, each a **seamless horizontal loop** (487 px wide or a multiple): sky, far canopy, mid trees, foreground leaves and vines.
- **Biomes (4):** Twilight Jungle, Misty Bog, Overgrown Ruins, Moonlit Canopy.
- **Tiles 16×16**, about 30 per biome: ground top and fill, gap edges, slopes, platform caps, decor (mushrooms, bones, flowers).
- **Obstacles** (separate sprites, re-dressed per biome): fallen log, thorny gap edge, root snare (snap [2]), low branch, critter (a Gloomling runner [4]), and a **vine anchor with a faint glow** (sway [3]).
- **Treasure clearing:** a mossy glade with fireflies and a **glowing chest** (closed, opening [4], open).
- **The home icon** and the "rotate phone" icon are UI (§14).
- Biome transitions are a gentle fade at a clearing (no transition art).

---

## 11. Cave Delve

16 chamber backdrops (wide fight scenes: Skerbie on the left, enemies on the right), plus a shared **descending-stairs transition** [6].

| Zone (floors) | Look | Backdrops |
|---|---|---|
| Root Hollows (1–5) | twisting roots, glowing fungi, dripping water | 2 fight chambers, 1 treasure room, 1 boss chamber |
| Crystal Caverns (6–10) | jagged crystals pulsing with light, echoing dark | same |
| Sunken Ruins (11–15) | ancient carved halls, broken statues, faint purple rune-light | same |
| Hollow Deep (16+) | black stone, drifting smoke, the Hollow's home turf | same |

**Treasure room:** a glowing chest on a pedestal, scattered coins. **Boss chambers** are bigger and more dramatic.

---

## 12. Effects library (shared; small + large sizes for combat and element effects)

- **Elements (fire, water, lightning, earth, ice), each:** hammer impact [5], ground-miss splash [4], enemy aura loop [3].
- **Mind (purple):** spell-cast burst [5], projectile [3 loop], impact [4].
- **Strength:** ground-slam shockwave [5], armor-up shimmer [4].
- **Speed:** slash arc [3], afterimage trail [3].
- **Signature smoke:** idle wisps [4 loop], power-up flare [5] (tints toward the element or type in use), speed trail [3].
- **General:** hit spark [3], crit flash [3], parry flash [3], heal sparkle [4], patch-up bandage poof [4], coin pop [3], loot shine [4], "new thing" sparkle [4 loop], level-up burst [6], mini evolution smoke flash [6].
- **Evolution sequence** [~12]: white silhouette → light pillar with swirling smoke → burst reveal.
- **Druid summon ring** [5]. **Glow layers** for fire, lightning, magic and eye glow.

---

## 13. Items and icons (24×24)

**Rarity is shown by frame material:** rough wood (common), silver (rare), gold with a soft glow (epic). Make 3 frame sprites and draw each item icon to sit inside them.

- **Weapons (6)** and **armors (6)** (§5), **charms (~6):** fang, feather, eye stone, bone die, moon coin, ember shard.
- **Consumables:** health potion, power tonic, bomb, smoke bomb, snack.
- **Materials:** wood, stone, scrap.
- **Ingredients (6):** glowcap mushroom, ember pepper, moonberry, frostmint, ironroot, shadow plum.
- **Dye packs:** a pouch icon per finish (metallic, glow, two-tone, sparkle) + the smoke-zone pack.
- **Hats (~6):** an icon for each.
- **Currency:** coin icon (+ a stack variant).

**Garden plants (in the scene):** each of the 6 ingredients in **sprout → growing → ripe** (ripe gets a soft sparkle) = 18 sprites. **Overflow pile:** small, medium and heaped (3 sprites). **Merchant (NPC-FOX):** a hunched cloaked fox pulling a rickety cart covered in lanterns, trinkets and hanging bottles: arrive [4], parked idle [3] (leaving = arrive reversed).

---

## 14. UI

- **Panels** (stats, recap, chest, merchant, settings, dye studio): **dark carved wood + worn parchment with iron corner brackets**, as 9-slice sprites, slightly translucent.
- **Recap:** a **torn journal page** with small paw-scrawl doodles (icons for gathered, built, found, raid, overflow).
- **Stats:** 3 **carved grooves** that fill with color (Speed silver, Strength bronze, Mind purple), plus subtype rank pips.
- **Small hand-drawn pixel icons (16×16):** settings gear, home (Jungle Run exit), hint, rotate phone, sound on/off, music on/off, back, confirm, share/backup, restore, lock, skill point, level star.
- **Font:** one openly licensed (OFL) pixel font from Google Fonts, bundled locally. The art doesn't draw text.

---

## 15. Asset count summary

| Group | Count |
|---|---|
| Skerbie bodies | 8 (+ egg), ~35 animations each |
| Gear overlays | 6 weapons + 6 armors × 2 sizes; ~6 hats × 2 sizes |
| Home | 3 den tiers, 4 skies, 4 lighting overlays, 12 buildables × 3 tiers, scaffold + damage kit, crack, ambient sprites |
| Enemies | 9 regular + 3 bosses |
| Tavern | background, breakables, crowd, badger, druid, 5 beasts |
| Game scenes | Word Rush, Block Party (+ hammer, pads), Potion Brew, Rune Lock tiles, Forage |
| Jungle Run | 4 biomes × (4 parallax layers + ~30 tiles), obstacles, clearing chest |
| Cave Delve | 16 backdrops + stairs transition |
| Effects | full library (§12), small + large where noted |
| Icons and UI | ~60 item icons, 3 rarity frames, ~13 UI icons, 9-slice panels |
| NPCs | fox merchant + cart, badger, druid |

---

## 16. First test asset (do this first, then stop for approval)

**SKB-BABY, idle [4] + blink [2]**, 32×32, using the §4 character core + the baby description + the §2 dye-zone slots + the §3 palette. Deliver the sheet, an 8× preview, the GIFs, and `frames.json`, and view them before showing George. **Don't start the full order until he approves the look.**
