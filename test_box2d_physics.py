import unittest

import pygame

from Physics.box2d_world import Box2DPhysicsWorld


class DummyEntity:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, 20, 20)
        self.rect.center = (x, y)
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.angle = 0.0


class TestBox2DPhysics(unittest.TestCase):
    def test_fixed_step_is_stable_for_same_total_time(self):
        e1 = DummyEntity(100, 100)
        e2 = DummyEntity(100, 100)

        w1 = Box2DPhysicsWorld(fixed_dt=1.0 / 60.0, max_substeps=10)
        w2 = Box2DPhysicsWorld(fixed_dt=1.0 / 60.0, max_substeps=10)

        b1 = w1.add_circle_body(e1, radius_px=10, mass=1.0)
        b2 = w2.add_circle_body(e2, radius_px=10, mass=1.0)

        b1.linearVelocity = (4.0, 0.0)
        b2.linearVelocity = (4.0, 0.0)

        w1.step(0.05)
        for _ in range(3):
            w2.step(0.05 / 3.0)

        self.assertAlmostEqual(e1.pos.x, e2.pos.x, delta=1.0)
        self.assertAlmostEqual(e1.pos.y, e2.pos.y, delta=1.0)

    def test_explosion_impulse_pushes_outward(self):
        e = DummyEntity(120, 100)
        w = Box2DPhysicsWorld()
        body = w.add_circle_body(e, radius_px=8, mass=1.0)

        self.assertAlmostEqual(body.linearVelocity.x, 0.0, delta=1e-6)
        w.apply_explosion_impulse(center_px=(100, 100), radius_px=80, impulse_strength=15)
        w.step(1.0 / 60.0)

        self.assertGreater(e.vel.x, 0.0)

    def test_metrics_present_after_step(self):
        e = DummyEntity(50, 50)
        w = Box2DPhysicsWorld()
        w.add_circle_body(e, radius_px=8, mass=1.0)
        w.step(1.0 / 60.0)

        m = w.get_metrics()
        self.assertIn("physics_step_ms", m)
        self.assertIn("substeps", m)
        self.assertIn("contacts", m)


if __name__ == "__main__":
    unittest.main()
