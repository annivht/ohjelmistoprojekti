# RocketGame.py — Summary and Review

**Overview:**
- File: RocketGame.py
- Purpose: Main game script implementing game loop, asset loading, spawn/wave system, collision handling, HUD, menus and integration with player/enemy classes and helpers.

**Quick facts:**
- Runs a full pygame game loop.
- Uses many external modules and classes (Players, Enemies, ExplosionManager, Points, UI helpers, SpriteSettings, planets, spatial collisions).
- Heavy use of globals and try/except blocks for robustness in varying resource environments.

**Contents (high-level):**
- Imports and module-level constants
- Asset loading (background, planets, enemy images, boss image, explosion frames, player frames, health UI)
- Managers and helpers instantiation (ExplosionManager, SpatialHash, SpriteSettings)
- Global state: enemies, enemy_bullets, muzzles, player, wave system, HUD state
- Functions: `apply_hitbox`, `clear_round_state`, `reset_game`, `restart_current_wave`, `spawn_inside_edge`, `spawn_wave`, `force_unstick`
- Main loop: event handling, updates, drawing, collisions, menus, pause, explosions, UI

**File:** [RocketGame.py](RocketGame.py)

**Imports (top-level):**
- stdlib: `sys`, `os`, `random`
- third-party: `pygame`
- local modules / classes: 
  - `SpriteSettings` (SpriteSettings)
  - `Player`, `Player2` (from `Player` and `player2`)
  - `MainMenu`, `NextLevel`, `GameOverScreen` (from `Valikot`)
  - `ExplosionManager` (from `explosion`)
  - `SpatialHash`, `apply_impact`, `separate`, `_get_pos`, `get_collision_radius` (from `collisions`)
  - `init_enemy_health_bars` (from `ui`)
  - `Points` (from `points`)
  - Enemy classes: `StraightEnemy`, `CircleEnemy`, `DownEnemy`, `UpEnemy` (from `Enemies.enemy`)
  - `BossEnemy` (from `boss_enemy`)
  - `planets` module
  - optionally `Ammus` (wrapped in try/except)

**Module-level constants & toggles:**
- Window & HUD:
  - `X = 1600`, `Y = 800`
  - `HEALTH_ICON_SIZE`, `HEALTH_ICON_MARGIN`, `HEALTH_ICON_SCALE_SIZE`, `HEALTH_ICON_POS`
- Hitbox overrides:
  - `HITBOX_SIZE_PLAYER = (64, 64)`
  - `HITBOX_SIZE_ENEMY = (48, 48)`
  - `HITBOX_SIZE_BOSS = (140, 140)`
- Collision and debug toggles:
  - `USE_SPATIAL_COLLISIONS = True`
  - `DEBUG_DRAW_COLLISIONS = True`
- Wave system:
  - `current_wave`, `MAX_WAVE = 4`, `wave_cleared`, boss delay timers

**Global state variables (not exhaustive):**
- `screen`, `tausta`, `planeetat`, `planeetta_paikat`, `tausta_leveys`, `tausta_korkeus`
- `enemy_imgs`, `boss_image`
- `explosion_manager`
- `spatial_hash`, `collisions`
- `enemies`, `enemy_bullets`, `muzzles`
- `player`, `player_ship`, `player_start_x`, `player_start_y`, `player_scale_factor`
- `pistejarjestelma` (Points instance), `lives`, `enemy_hit_cooldown`

**Functions (signatures + responsibilities):**
- `apply_hitbox(obj, size=None)`
  - Purpose: applies a rectangular hitbox size to `obj.rect` while preserving center; syncs `obj.pos` and sets `obj.collision_radius` where possible.
  - Notes: silently returns when `size` is `None` or on any exception.

- `clear_round_state()`
  - Purpose: Clears `enemies`, `enemy_bullets`, `muzzles`, `collisions` and tries to clear `player.weapons.bullets`.

- `reset_game()`
  - Purpose: Full reset of the game: waves, player health/pos/vel, clears state and respawns wave 1. Resets score (Points instance).

- `restart_current_wave()`
  - Purpose: Clears in-progress objects and respawns the same `current_wave`; resets player health/pos/vel.

- `spawn_inside_edge(edge, inset=80)`
  - Purpose: Returns a spawn (x,y) coordinate inside the chosen screen edge with `inset` margin.
  - Supported edges: `left`, `right`, `top`, `bottom`.

- `spawn_wave(wave_num)`
  - Purpose: Builds the enemy list for the supplied wave number. Behavior per-wave:
    - Wave 1: two enemies (StraightEnemy and CircleEnemy), uses `SpriteSettings` frames if available.
    - Wave 2: spawns enemies at edges, gives random initial velocity.
    - Wave 3: spawns 5 enemies, some moving down and some moving up.
    - Wave 4: spawns a `BossEnemy` (hp=12) and applies boss hitbox.
  - Applies `apply_hitbox` to spawned enemies and sets `collision_radius`.

- `force_unstick(a, b, eps=2)`
  - Purpose: If two rects overlap exactly, nudge them apart along the center-to-center vector and sync `pos` attributes.

**Main game loop responsibilities (high level):**
- Event handling (quit, pause via ESC)
- Timing: `dt = clock.tick(60)`
- Update:
  - `planets.update_planet(dt)`
  - `player.update(dt)` and keep player inside world
  - Update enemy AI and let enemies shoot (`maybe_shoot`)
  - Spatial collisions (optional) between enemies (rebuilds spatial hash, queries possible pairs, uses circle overlap tests, calls `apply_impact` and `separate` with iterative separation)
  - Bullet/enemy collision checks (player bullets vs enemies): spawn explosions, remove enemies or deduct HP for boss
  - Enemy bullets vs player: explosion, deduct health
  - Enemy-player direct collisions: compute separation, apply impulses, apply damage and cooldown
- Drawing:
  - Camera transform & background blitting
  - Planets, enemies, player
  - Draw health/hud and scores
  - Explosion manager updates/draw
  - Debug overlays (collision rects and radii)
- Menus: main menu at start, NextLevel when boss cleared, PauseMenu, GameOverScreen handling

**Debugging & overlays:**
- `DEBUG_DRAW_COLLISIONS = True` draws rect outlines and collision radius circles for player and enemies.
- Print debug messages occasionally (e.g. `PLAYER DAMAGE` diagnostic print).

**Explosion & sprite loading behavior:**
- Uses `ExplosionManager` and attempts to populate `frames_by_type` for `boss`, `enemy`, `player` by scanning `enemy-sprite/PNG_Parts&Spriter_Animation/Explosions` and `alukset/alus/*/Destroyed`.
- Falls back to generic frames if type-specific frames are missing.
- Loads enemy sprite sheets from `images/viholliset` and scales them to (64,64).

**Try/except usage — findings & recommendations:**
- Pattern: Many `try: ... except Exception: pass` blocks across file. This is defensive but can silently hide errors. Examples include:
  - `try: player = Player2(...) except Exception: ...` — here the fallback prints traceback and falls back to `Player` (good), but other blocks are silent.
  - Asset loading fallbacks (explosion frames, planet init): many `except Exception: pass` which will suppress filesystem or loader errors without logging.
  - Multiple places: `try: ... except Exception: pass` around UI init, `init_enemy_health_bars`, `planets.init_planet`, `explosion_manager` usage etc.

- Specific issues found (concrete):
  - Duplicate call: `apply_hitbox(e, HITBOX_SIZE_ENEMY)` is called twice in Wave 2 for each spawned enemy (likely accidental duplication).
  - `spawn_inside_edge('top')` returns (random_x, inset) using `tausta_leveys` for x range and `inset` for y — that's correct. Just verify intended ranges. (No direct bug here.)
  - Many `except Exception:` swallow all errors. This can make debugging very hard when resources are missing or an unexpected runtime error occurs.
  - Some `try` blocks attempt to set attributes like `collision_radius` and silently ignore failures — these should log at least a warning.

- Recommendations for try/excepts:
  1. Replace broad `except Exception:` with targeted exceptions where possible (e.g., `FileNotFoundError`, `pygame.error`).
  2. When catching exceptions intentionally, at minimum `logging.exception()` or `print()` with context should be used so failures are visible during development.
  3. Avoid swallowing exceptions in code paths that are essential (asset loading, core logic). Use fallbacks but log why fallback was used.
  4. For debug-only tolerant behavior, consider a `--strict` or `DEBUG` flag to optionally re-raise errors during development.

**Concrete suggestions / small fixes**
- Remove duplicated `apply_hitbox` in Wave 2 (one of them is redundant).
- Replace silent exception blocks with logging; e.g.:
  - `except Exception:` -> `except Exception as exc:` then `import traceback; traceback.print_exc()` or `logging.exception("...")`.
- Consolidate explosion frame loading and avoid repeated existence checks for the same folder; use helper function that returns frames or None.
- Centralize asset loading into functions like `load_enemy_images()`, `load_explosion_frames()` and unit-testable pieces.

**Refactor recommendations (medium/large):**
- Break the monolithic script into modules:
  - `assets.py` — load and cache images, frames, SpriteSettings, explosion frames
  - `spawn.py` — wave definitions and spawn helpers
  - `ui_manager.py` — HUD rendering, menus wrappers
  - `game_state.py` — stateful globals wrapped in a `GameState` object (player, enemies, bullets, scores, timers)
  - `main.py` — small runner that sets up pygame and runs the loop using `GameState` + managers
- Reduce global variables by bundling into dataclasses or a `GameState` class.
- Use an event-driven or ECS-like pattern for collisions and effects (optional, more architecture changes).

**Checklist of items included from RocketGame.py**
- Classes-in-use: `Player`, `Player2`, `StraightEnemy`, `CircleEnemy`, `DownEnemy`, `UpEnemy`, `BossEnemy`, `ExplosionManager`, `Points`, `SpatialHash`
- Functions implemented in file: `apply_hitbox`, `clear_round_state`, `reset_game`, `restart_current_wave`, `spawn_inside_edge`, `spawn_wave`, `force_unstick`
- Global toggles: `DEBUG_DRAW_COLLISIONS`, `USE_SPATIAL_COLLISIONS`
- Wave logic (1..4), boss handling, menu transitions (MainMenu, NextLevel, GameOverScreen, PauseMenu)

**Next suggested actions (I can do these if you want):**
- I can create a small patch fixing the duplicated `apply_hitbox` call in Wave 2 and add logging to a few critical try/except blocks.
- I can extract the long `spawn_wave` into a dedicated `spawn.py` module and wire it back in.
- I can run `python -m pyflakes`/`flake8`/`tests` to find other issues if you want.

---

If you'd like, I can now:
- apply small automated fixes (remove duplicate call + add logging), or
- split the file into modules as described.

Which next step should I take? (I can start with the duplicate fix and safer exception logging.)
