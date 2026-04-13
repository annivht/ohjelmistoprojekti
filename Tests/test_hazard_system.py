import os
import sys
import unittest

import pygame


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

SPRITE_ROOT = os.path.join(PROJECT_ROOT, "images", "Space-Shooter_objects")

from Hazards.hazard_system import HazardSpriteLibrary, HazardSystem, MeteorHazard


TEST_HAZARD_CONFIG = {
    "enabled": True,
    "meteor_spawn_rate": 9999.0,
    "enemy_drop_chance": 0.0,
    "pickup_drop_chance": 0.0,
    "boss_drop_interval_min": 9999.0,
    "boss_drop_interval_max": 9999.0,
}


class DummyPlayer:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, 40, 40)
        self.rect.center = (x, y)


class DummyBullet:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, 8, 8)
        self.rect.center = (x, y)


class TestHazardSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_bomb_explodes_after_fuse(self):
        hs = HazardSystem(world_size=(800, 600), sprite_root=SPRITE_ROOT, config=TEST_HAZARD_CONFIG)
        player = DummyPlayer(10, 10)
        bullets = []
        hs.spawn_bomb((220, 220))

        # Simulate a bit more than fuse time (3.0s + idle transition margin).
        total_ms = 0
        exploded = False
        saw_shockwave = False
        while total_ms < 3700:
            effects = hs.update(100, player, bullets, boss_positions=[])
            total_ms += 100
            if hs.bombs and hs.bombs[0].is_exploding:
                exploded = True
            if effects.get("shockwaves"):
                saw_shockwave = True
            if exploded and saw_shockwave:
                break

        self.assertTrue(exploded)
        self.assertTrue(saw_shockwave)
        self.assertIn("countdown_tick", effects)

    def test_bomb_damage_only_inside_radius(self):
        hs = HazardSystem(world_size=(800, 600), sprite_root=SPRITE_ROOT, config=TEST_HAZARD_CONFIG)
        bullets = []

        near_player = DummyPlayer(200, 200)
        hs.spawn_bomb((200, 200))
        near_damage = 0
        for _ in range(40):
            fx = hs.update(100, near_player, bullets, boss_positions=[])
            near_damage += int(fx.get("player_damage", 0))
        self.assertGreaterEqual(near_damage, 1)

        hs = HazardSystem(world_size=(800, 600), sprite_root=SPRITE_ROOT, config=TEST_HAZARD_CONFIG)
        far_player = DummyPlayer(700, 500)
        hs.spawn_bomb((200, 200))
        far_damage = 0
        for _ in range(40):
            fx = hs.update(100, far_player, bullets, boss_positions=[])
            far_damage += int(fx.get("player_damage", 0))
        self.assertEqual(far_damage, 0)

    def test_meteor_split_on_destroy(self):
        sprites = HazardSpriteLibrary(SPRITE_ROOT)
        meteor = MeteorHazard(center=(350, 300), velocity=(100, 0), tier=3, sprites=sprites)

        # Tier 3 has hp 3, so destroy it with three hits.
        self.assertFalse(meteor.take_hit(1))
        self.assertFalse(meteor.take_hit(1))
        self.assertTrue(meteor.take_hit(1))

        children = meteor.split_children()
        self.assertEqual(len(children), 2)
        self.assertTrue(all(ch.tier == 2 for ch in children))


if __name__ == "__main__":
    unittest.main()
