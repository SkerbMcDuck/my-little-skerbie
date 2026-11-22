# Pocket Monster Game: Spec (in progress)

Target: jailbroken iPhone X (iOS 16.7.8), Safari, portrait. No data plan.

## Decided
- **Neglect:** no death and no runaway. He has needs and can get sick, but progress is never lost. Growth can pause.
- **Care actions:** feed, teach, train, plus upkeep (still being decided).
- **Train = mini-games.** Several high-quality, varied games (brain, dexterity, and so on). Treat these as the core of the game.
- **Multiplayer idea:** fight other people's monsters, or team up against a horde. Battles are AFK.

## Question queue (one at a time, then one follow-up each)
1. Q1 Hosting: GitHub Pages, works offline
2. Q2 Original creature with care-based evolutions
3. Q3 Real-time needs, slow decay
4. Q4a What pauses growth
5. Q4b What causes sickness
6. Q5b Upkeep: clean / medicine / sleep
7. Q6a One game per stat (Speed / Power / Guard / Smarts)
8. Q6b The four v1 games (Rockfall, Power Swing, Copycat, Block Party)
9. Q6c Difficulty scaling and score-based gains
10. Q6d Training costs energy and hunger
11. Q6e Sound plus mute
12. Q7 No notifications
13. Q8 Toy-shell look
14. Q9 Phone only (not CarPlay)
15. Q10 v1 finish line
16. Q11 Multiplayer in v2
17. Q12 Monster codes (offline multiplayer)
18. Q13 Solo AFK horde in v1
19. The 9 subtypes and which game goes with each
20. Training session structure: how many games per session, and how long
21. How category scores become forms (map the 8-form tree onto 3 types)
22. How many of the 9 games ship in v1
23. What he does while you're away (activities, and the environment changes you can see)
24. Items: what kinds, and what they do in battle
25. Balance: how away-progress compares to game boosts
26. Make the three type extras equally valuable (no "best" type)
27. Cave Delve: the player-started adventure where you control or help him fight (replaces live raids)
28. (done) Q10 (v1 finish line), moved here because it depends on 19–27
29. The v1 game list (pushed here by George). Proposed 6: Rockfall and Quick Draw (Speed), Power Swing and Block Party (Strength), Copycat and Odd One Out (Mind)
30. The baby's type and moves, before the kid form sets his type
31. (done) How the secretly educational design works (adaptive difficulty, progress tracking)
32. The Mind game lineup (trivia, math, logic, with an alchemy theme)
33. The Strength lineup (club swing, beast wrestle, and is Block Party kept?)
34. (deferred with Spellbook) Where trivia and question content comes from (an original bank, fact-checked)
35. (done) The v1 game count: 10–11 games is a lot to polish. Trim or keep all?
36. (deferred) Whack-a-mole game details
37. Beast Wrestle details
38. Potion Brew and Rune Lock details
39. (done) Money: what coins buy, and where else they're earned
40. (done) The tavern: only this game's backdrop, or a place in his world?
41. (done) The 9 subtypes: what each does, and what skill points buy
42. (done) Teach: how moves are learned (cost, how many he can know)
43. (done) First launch: naming him, the egg, the first session
44. (done) Save safety: backup and restore, since saves live only on the phone
45. (done) Max level: is there one (George said "before max level", but earlier it was "no cap")? Subtype rank caps, and the pacing to max everything
46. Skerbie's base look (it drives every frame description in the art spec)
(new questions get added to the end)

## Jungle Run (Speed), locked
- An auto-running side-scroller: tap to jump, hold to swing from vines. Obstacles are logs, gaps and critters. It speeds up over time.
- A treasure clearing about every 30 seconds: a short safe break for loot. He **keeps running automatically**. A small **home icon** (always visible) ends the run and keeps everything.
- Loot gets bigger at later clearings. A fall keeps everything from reached clearings and loses only the current stretch.
Note: Q20 (session structure) was answered by Q19. Q22 (how many games) is merged into Q29.
Note: Q8 (a toy shell with 3 buttons) conflicts with tap-to-interact. Revisit it.
Note: raids may cover Q13 (solo AFK horde). Check when we get there.

## Answers log
- **Strength game 2 = BAR BRAWL** (replaces Beast Wrestle): a tavern bar fight vs summoned beasts; hit timing and parries are key. 1v1 side view; the beast telegraphs (windup + eye flash); tap on the strike to parry; a perfect parry = stagger + a counter window of timed combo taps; feints and variable timing (not a beat, distinct from Block Party); KO before ~30 seconds; score = perfect parries + combo damage + speed; winning pays coins.
- **Orientation:** portrait everywhere except **Jungle Run, which plays in landscape.** (Art A2 follow-up.)
- Working title: **My Little Skerbie**. Never call it "pocket monster".
- Q1: Hosted on GitHub Pages, works offline, saves on the device. Its own new repo, `my-little-skerbie`, separate from carplay-screen-tester.
- Q2: Original creature that hatches from an egg. Forms branch by training at every stage of growth, not only at adult.
- Q2 follow-up: v1 tree is egg, 1 baby, 2 kids, 5 adults. How it maps onto 3 types is still open (Q21).
- **Training trains all aspects every session.** The player is scored in each category, and those scores shape how the Skerbie changes, so growth is tied to the player's own skill.
- **Stat structure:** 3 main types (Speed / Strength / Mind), each with 3 subtypes. Mini-games are linked to subtypes.
- Q3: Real time. Each need drops fast at first and then slows, so there's daily urgency without frustration. Exact timing still to tune.
- Q3 follow-up: **No regression.** While you're away he keeps working, with slow progress. The games give the real boosts. His time away shows when you come back: he changes his environment and finds items for battle, and so on.
- Q4a: **He takes care of himself, survival-game style.** The games raise his skills and overall level, which makes him better at self-care, which speeds up his away progress. Needs set his work rate.
- Q4a follow-up: **Basic self-care (eating, cleaning, resting, healing) runs on OVERALL level, never on one type**, so a player who's weak at one game type is never locked out. Types only shape the extras: Strength builds and gathers more, Speed finds rarer items, Mind crafts better food and medicine. Self-care caps around 80%, so player care always adds something.
- Q4b: **No sickness. Raids instead.** Enemies attack while you're away. He's always meant to lose eventually, and his skills decide how long he lasts. You come back to fix him and his place up, plus XP and loot for every enemy he beat before they got him.
- Q4b follow-up: At most 1 raid a day, only while the app is closed. Waves get tougher, and his stats decide how many waves he survives. A raid report on return shows waves survived, enemies beaten, XP and loot. He's knocked out and away progress pauses until a one-tap patch-up. Home damage repairs over time, or faster with materials. Nothing is ever destroyed for good.
- Q5b: Player actions are feed, train, teach, and patch up. **No buttons: you tap things in the scene to interact.**
- Q5b follow-up: Side-view home scene. Food bowl or pantry = feed. Training spot = train. Chalkboard or bookshelf = teach. Tap him = pet him (or patch him up after a raid). Hold on him = stats and level. Things he builds or finds also appear in the scene and can be tapped. Anything new gets a bounce or sparkle.
- Q6c: Games get harder as his related stats rise. Gains = score × difficulty. The baby stage is forgiving, for learning the games.
- Q6c follow-up: No personal bests, since difficulty always rises. Simple rule: more play = more XP.
- Q6d: No daily cap. Training tires him. **A worn-out Skerbie can't train again until you feed him.** This only applies while you're playing.
- Q6d follow-up: About 3 training sessions wear him out. The pantry is stocked by what he gathers while you're away, and there's 1 free snack from you when it's empty. **Foraging:** tap the door for a relaxed mini-game (catching falling fruit) that earns food, not XP, about 1 training round's worth per forage. Later a **garden** (built through Strength) grows food passively.
- Q6e: Chiptune sound effects, his voice chirps, a home tune, and separate sound and music toggles on a tappable radio. **It won't live on Safari forever, so plan for haptics:** every "feel" moment calls a haptics hook that does nothing today and gets wired to real vibration later.
- Q6e follow-up: **Build as a Capacitor app from day one** (it supersedes Q1's GitHub Pages hosting), because the X is what he'll play on and it's offline. Same web code underneath. Real haptics (Capacitor Haptics), and local notifications become possible with no server.
- Q6e follow-up 2: GitHub Actions builds the iOS app (public repo, no secrets), installed on the X with AppSync. **The same code is also published on GitHub Pages**, so it can be tested in Safari on his real iPhone 17 (no sideloading on the 17) and on his PC.
- **Raid notifications:** a notification lets you pop in and help or control him during the raid. He lasts longer and you earn more. (Q27)
- Test panel: lives in Settings, not hidden, **web version only**. It can skip time, trigger a raid, fill the pantry, and jump a growth stage. Test saves on the 17 are separate. The X app has no test panel.
- Q7: **Raid notifications only.** Super easy to turn off, never annoying.
- Q7 follow-up: **Changed.** Raids stay random and AFK, and you don't join them live. So no raid notifications (dropped unless George says otherwise). The hands-on fight content is a separate **Cave Delve** that the player starts manually. (Q27 is now about the Cave Delve.)
- Q8: Full-screen pixel-art home scene, with lighting that follows the real time of day and a home that grows as he builds. **George wants good art, so sourcing must be done right.**
- Q8 follow-up: The world, items and enemies come from a licensed itch.io pack (the license must allow commercial use). Skerbie's 8 forms get commissioned from a pixel artist after v1 plays well. Placeholders until then. v1 ships an **art spec** (sprite size, animation frames, file layout) so real art drops right in. No AI-generated art for Skerbie.
- Q9: Don't design for CarBridge or the car at all. Ignore it.
- Q11: Multiplayer in v2. v1 stores stats, moves and items in a battle-ready format.
- Q11 follow-up: One shared battle engine for raids, the Cave Delve, and v2 multiplayer.
- Q12: **All multiplayer waits until after the game is App Store ready.** Not specced now. (Q13 solo horde is covered by raids, so it's dropped.)
- Q19: **A session = 3 games in a row (1 Speed, 1 Strength, 1 Mind), about 30 seconds each.** Each score gives XP to its main type (driving level and evolution). He also earns **free skill points** to spend on the 9 subtypes. Each type has a pool of games, and one is picked per session.
- Q21: 8 forms: egg, 1 baby, 3 kids, 4 adults (Speed, Strength, Mind, Balanced). The kid form = the type with the most XP during the baby stage. The adult form = the type with the most XP during the kid stage, or Balanced if no type clearly leads. Hybrids come later.
- Q21 follow-up: Growth is by overall level. The egg hatches minutes after start (tap to crack). Kid at level 5 (about 2–3 days), adult at level 15 (about 2 weeks). No level cap after adult. Each evolution is a big flash-and-reveal moment. The levels are tunable in the settings block.
- Q23: While you're away he loops through gathering (food and materials), building (home upgrades that show up in the scene and can be tapped), exploring (items for raids and the Delve), and resting (when tired or hungry, which slows progress). A quick "while you were gone" recap card greets you on return.
- Q23 follow-up: Materials are wood, stone and scrap. v1 builds: bed (faster rest), garden (passive food), pantry shelf (more food storage), workbench (crafts items), walls and traps (last longer in raids), training gear (more XP for one type each), lantern and decorations (flavor). He picks builds himself. The player can choose his next project on a tappable **blueprint board**.
- Q24: Gear has 3 slots (weapon, armor, charm) with stat boosts and small visual changes. Consumables (potions, bombs, snacks): he auto-uses them in raids, and the player uses them in the Delve. 3 rarities (common, rare, epic). Sources: exploring, raid and Delve rewards, workbench crafting. Hold an item to see its info.
- Q24 follow-up: The chest starts at 20 slots and grows with upgrades. Unwanted gear can be scrapped for scrap material. Overflow goes to a **pile outside the door** (last 10 items, 24 hours). Tap it to reclaim, and leftovers auto-scrap into materials after that.
- Q25: 1 training session ≈ 2 hours of away progress. Away progress builds for up to 24 hours, then he waits (nothing lost). Away efficiency scales with level and self-sufficiency.
- Q25 follow-up: The 24-hour cap limits forward clock jumps. Backward jumps are ignored. No punishment. The web test panel is the legit time skip.
- Q26: George rejected "Speed finds / Strength earns / Mind crafts" because it locks types out of play styles. Raids are a big part of time away, so they can't favor Strength.
- Q26 take 2: **"Type changes style, not power."** Every type does everything (raids, exploring, crafting, gathering). Overall level sets power. At most about a 10% specialty edge. Raids are tuned so all types survive about equally at the same level. **Mind = magic: alchemy, spells and strategy.**
- Q26 follow-up: Magic and alchemy are Mind-only (spells, brewing potions mid-fight, traps, reading enemy patterns). Strength gets power techniques (slams, armor-up stances, shrugging off hits). Speed gets tricks (combos, dodges, stealing an enemy's item). Taught moves come from his type's list plus a few shared basics.
- Q27: The **Cave Delve** entrance appears in the scene at the kid stage and costs 1 meal of energy. Floors of fights, with a treasure room every few floors. Deeper means tougher enemies and better loot. Semi-auto fights: he fights on his own, and the player taps charged moves and items. Leave between floors anytime. If knocked out, the run ends but **all loot so far is kept**. Best depth is recorded.
- Q27 follow-up: Floors take 30–60 seconds, and runs last 3–5 minutes. Every run starts at floor 1, and already-cleared floors go fast. A cave knockout needs the same one-tap patch-up as a raid before he can train or delve again.
- Q30: **The baby stage is short.** He should look different after the first session. As a baby he fights other babies, so raid enemies match his stage.
- Q30 follow-up (**supersedes the Q21 follow-up's "kid at level 5"**): The egg hatches within about a minute (tap to crack). The baby plays the first training session, then evolves to a kid right after it. **The kid form always matches whichever type currently has the most XP** and switches (with a mini evolution moment) whenever another type takes the lead. The form locks permanently at adult (level 15, about 2 weeks). The Delve unlocks at kid, and he learns his first signature move then. Enemies scale to his stage (baby raiders for a baby, and so on).
- Q29: v1 games: Rockfall and **a typing game (replaces Quick Draw)** for Speed, Power Swing and Block Party for Strength, Copycat and Odd One Out for Mind. Each session picks 1 game per type at random.
- Q29 follow-up: **Word Rush.** Enemies charge from the right with words over their heads, and typing a word knocks that enemy back. Played in the top half (the keyboard covers the bottom). Autocorrect off. Letters light up as they're typed correctly. Typos flash red and play continues. Words are game-themed and get longer and faster with Speed, with several enemies at once later.
- **Game changes (George, after Q29):**
  - Mind games should be trivia, math, puzzle and logic-puzzle style, leaning on the magic and alchemy theme.
  - Power Swing becomes swinging a bat or club at a target, golf-style.
  - Another Strength game is about stamina: arm-wrestling or wrestling a larger beast, tapping to sustain power.
  - **Low-key educational:** not advertised, but every game also trains the player (typing, trivia, logic, and so on).
- Q28 (v1 milestones) is still awaiting an answer.
- Q32: Mind v1 = **Potion Brew** (math: tap numbered ingredients to hit an exact magic number, from adding up to multi-step) and **Rune Lock** (logic: slide or rotate runes to complete a pattern and open a seal). **Spellbook (trivia) is held back for now, but George wants it back soon after v1.**
- **v1 = 2 games per type, 6 total:**
  - Speed: **Word Rush** and **Jungle Run**
  - Strength: **Block Party** (reworked as a rhythm game, DDR / Guitar Hero style) and **Beast Wrestle**
  - Mind: **Potion Brew** and **Rune Lock**
  - Block Party (locked base): he stands in the center. Enemies march in from 4 directions on a chiptune beat. Hit rings around him, graded Perfect/Great/Good/Miss with Perfect combos. A miss means a flinch, and the song continues. Higher Strength means faster songs, more enemies, and doubles. A round is one 30–40-second song. **Elemental hammer:** he swings a hammer, and you tap the element that counters the incoming enemy. Element effects show when the hammer hits an enemy, or on the ground on a miss. (It's a Strength power technique, not magic.) Controls: 4 small element pads in a diamond in the bottom-third thumb zone, colors matching the enemies. Counter chain: Ice enemy→Fire, Fire enemy→Water, Water enemy→Lightning, Lightning enemy→Earth. Early on each direction keeps a fixed element. Later, elements mix across directions.
  - **SUPERSEDED, now Bar Brawl (see ART.md / below):** Beast Wrestle (old): locked arms with a bigger beast, with a power bar in the middle. Tap to push. The beast surges (growl and flash warning), and you tap harder through it. Steady rhythm builds a grip bonus, and frantic mashing slips. Pin it before about 30 seconds. Score = time to win + power held. Higher Strength brings bigger beasts with sneakier surges. Tap anywhere, as long as it can't trigger anything else. **Setting: a tavern arm-wrestling event** against wild, fantastical beasts (not raid enemies). He wrestles for money and **earns coins when he wins**.
  - Potion Brew (locked): a cauldron shows a target number. A shelf of 6 numbered ingredients sits below. Tap to add, and the total updates live. An exact hit bubbles over and scores. Overshooting fizzles and restarts that potion. Brew as many as possible in 30 seconds. Score = speed + low waste. **The math adapts to the player** (small adding, then bigger numbers, then subtracting "cursed" ingredients, then multipliers like "×2 dragon scale"). Higher Mind only shrinks the timer. **No single undo:** tapping the cauldron dumps the whole potion to start it over.
  - Rune Lock (locked): a grid of rune tiles (starting 3×3), each carrying a piece of a glowing line. Tap to rotate. Connect the flow from the source rune to the seal, the seal bursts, and a new grid slides in. As many seals as possible in 30 seconds, with fewer wasted rotations scoring higher. **Adapts to the player:** 4×4 and 5×5 grids, decoy dead ends, branches feeding 2 seals, locked tiles. Generated on the fly and guaranteed solvable. Higher Mind only shrinks the timer. **Hints are opt-in:** after about 8 seconds without progress, a small hint icon appears. Tapping it makes one wrong tile shimmer and costs points. Ignoring it costs nothing.
- Q39 Coins: **no real money, ever.** Earned from tavern wins (main), plus raids, the Delve and item sales. Spent on cosmetics, **dye packs** (unlock a pack, pick a color from a color-wheel palette, save it, and it's yours; more unlock over time, to color your Skerbie however you want), home items, and buying ingredients. Garden ingredients can be sold. A traveling merchant cart visits (tap to shop).
- Q39 follow-up (dyes): **Any color the player wants**, via a full color wheel plus **hex code entry**. Dye zones: main body, belly and markings, eyes (gear later). Since every color is free to make, **dye packs unlock finishes and extras** instead (metallic, glow, two-tone/gradient, sparkle, plus more saved-swatch slots and new dyeable zones). Saved swatches are reusable forever. **Art spec: sprites drawn with marked color zones** so dyes swap cleanly.
- Q40: In v1 the tavern is **only the backdrop for Beast Wrestle** (a crowd, a bartender paying the prize coins, a druid ringmaster bringing the beasts). It may become a visitable place later. Reconfirmed: each session = 1 random game from each type's pool, so his type emerges naturally from how you play.
- Q41 Subtypes (skill points, about 1 per training session, spent on the stats screen by holding on him; small permanent boosts, each useful to every type): Speed: **Reflex** (acts first), **Agility** (dodges), **Hustle** (explores faster while away). Strength: **Power** (hits harder), **Toughness** (less damage), **Stamina** (lasts longer in raids, needs less food). Mind: **Alchemy** (better crafting and potions), **Arcana** (stronger magic, slight boost to any type's specials), **Tactics** (smarter auto item use, faster move charge in the Delve).
- Q41 follow-up: **No respec. Builds can't go bad:** all 9 subtypes can realistically be maxed before max level, and order only changes how he feels along the way. Conflict: earlier "no level cap after adult" vs George's "max level". Queued as Q45.
- Q42: "Teach" was meant to be the sneaky-educational part. The games now do that job, so teach is to be scrapped or repurposed (being decided).
- Q42 follow-up: **Teach is scrapped for v1.** Moves unlock automatically by level ("he figured out a new move!" moment), from his type's list plus shared basics, at no cost. The **chalkboard** = where you choose his 4-move fight loadout. Later, the chalkboard becomes Spellbook's study spot (trivia unlocks bonus or secret moves).
- Q43 First launch: an egg in an empty den, which wobbles; tap a few times to crack it. He hatches, then naming (default "Skerbie", max 12 characters). The training spot sparkles for the first session. Each game shows a 3-second animated how-to the first time, with no text tutorials. Kid evolution right after. Den objects (bowl, door, chalkboard, and so on) each sparkle once when they become relevant. About 5 minutes total.
- Q43 follow-up: v1 = **one Skerbie.** The save format is ready for more. Later, adults find eggs, and you build up a **team**. Open problem (later): the same player's skills would push every Skerbie to the same type. Proposed timing (later): first new egg found once he's an adult (level 15), more at milestones (around 25, 40, 50). DECIDED (art A1): other species are dark animal humanoids (gorilla, croc, falcon, rabbit, elephant...), each with a type aptitude. Idea to explore: each egg has an innate aptitude that multiplies one type's XP, or types get judged against the player's own baseline.
- Q44 Save safety: Settings → "Back up Skerbie" exports the save as a file (to AirDrop to the 17 or the PC). "Restore Skerbie" imports it. Checksum validation rejects corrupted or tampered files. Plus **3 rolling auto-saves** kept internally that silently recover from a corrupted save. No accounts, no cloud. An in-app weekly backup reminder (not a notification) that can be turned off.
- Q45: **Max level 50.** Adult at 15. Each subtype caps at 10 ranks (90 points total). Points ≈ 1 per session + 1 per level-up, so everything is maxed around level 40. Level 50 takes about 2–3 months of regular play. Endgame: deeper Delve, tavern coins, rare loot, cosmetics and dyes, home building. All numbers tunable.
- Q28: v1 = 3 milestones, each playable on the X. (1) Core loop: hatch and naming, scene, feed/pantry/forage, 6 games, type XP and skill points and subtypes, kid lead-switching, leveling, sound and haptics hooks, Settings (and the web-only test panel), saves, auto-saves and backup, silent skill tracking, GitHub build (IPA + Pages). (2) Away loop: self-care and away progress (24-hour cap), gathering, building, blueprint board, garden, recap, battle engine with auto-raids and patch-up, items, gear, chest, overflow, workbench, coins, merchant, dyes. (3) Delve and adult: type moves and the chalkboard loadout, Cave Delve, adult evolution and lock, level 50 cap, tuning. Out of v1: multiplayer, teams, Spellbook, Whack-a-mole, Club Swing, achievements, visitable tavern.
- **CHANGE: George wants the real art done BEFORE the build starts** (it supersedes "placeholders first" from the Q8 follow-up). Next deliverable: a per-frame art spec with descriptions.
  - Held for later: Whack-a-mole, Club Swing, Spellbook (soon). Cut for good: Rockfall. Dropped: Quick Draw, Copycat, Odd One Out.
- **New Speed games (George):** a whack-a-mole style game, and a side-scrolling race (swinging from trees, jumping over things) that gets harder until you fail, with small treasure breaks along the way that reward progress and give natural stopping points.
- Q31: Every game trains a real skill. Two difficulty dials: his stats set the *pressure* (speed, timers, enemy count), and the *content* difficulty adapts to the player (aiming for about 75% success). **Skill tracking is completely hidden.** No visible Training Log, and the player is never told it's tracked. All data stays on the device. No educational branding anywhere.
- Q31 follow-up: **v1 just silently tracks the skills.** Achievements and rewards get worked out later. Nothing is shown to the player.
- George's note: the Q4a fix isn't complete, because the type extras are game-changing (rarer loot is clearly the best one). Queued as Q26.
- George's idea for Q19/Q22: maybe only 3 games (one per main type), with the points earned becoming skill points the player spends on subtypes as they choose.
- Superseded: Q6a (4 stats) and Q6b (4 games) are folded into Q19 and Q20.
