import time
from collections import deque

import pygame

from Physics.box2d_config import get_physics_profile

try:
    from Box2D import (
        b2CircleShape,
        b2ContactListener,
        b2_dynamicBody,
        b2Filter,
        b2_kinematicBody,
        b2_staticBody,
        b2Vec2,
        b2World,
    )
except Exception as exc:  # pragma: no cover - handled by caller
    raise RuntimeError("Box2D is required for Box2DPhysicsWorld") from exc


class CollisionCategory:
    PLAYER = 0x0001
    ENEMY = 0x0002
    PROJECTILE = 0x0004
    METEOR = 0x0008
    SENSOR = 0x0010


class ContactCollector(b2ContactListener):
    def __init__(self):
        super().__init__()
        self.begin_contacts = 0
        self.contact_events = deque(maxlen=64)

    def BeginContact(self, contact):
        self.begin_contacts += 1
        a = getattr(contact.fixtureA.body, "userData", None)
        b = getattr(contact.fixtureB.body, "userData", None)
        self.contact_events.append((a, b))

    def reset_frame_metrics(self):
        self.begin_contacts = 0


class Box2DPhysicsWorld:
    """Small adapter that keeps Box2D in fixed-step mode and syncs sprites."""

    PPM = 30.0  # pixels per meter

    def __init__(
        self,
        gravity=(0.0, 0.0),
        fixed_dt=1.0 / 60.0,
        velocity_iterations=8,
        position_iterations=3,
        max_substeps=5,
        profile_name="balanced",
    ):
        self.profile = get_physics_profile(profile_name)
        self.fixed_dt = float(fixed_dt)
        self.velocity_iterations = int(velocity_iterations)
        self.position_iterations = int(position_iterations)
        self.max_substeps = int(max_substeps)
        self.accumulator = 0.0

        self.world = b2World(gravity=gravity, doSleep=True)
        self.contact_collector = ContactCollector()
        self.world.contactListener = self.contact_collector

        self.entity_to_body = {}

        self.step_time_ms = 0.0
        self.last_substeps = 0
        self.frame_contacts = 0

    @classmethod
    def pixels_to_meters(cls, value_px):
        return float(value_px) / cls.PPM

    @classmethod
    def meters_to_pixels(cls, value_m):
        return float(value_m) * cls.PPM

    def add_circle_body(
        self,
        entity,
        radius_px,
        mass=1.0,
        dynamic=True,
        bullet=False,
        category=CollisionCategory.PLAYER,
        mask=0xFFFF,
        restitution=0.05,
        friction=0.2,
    ):
        x_px, y_px = self._entity_center(entity)
        body_type = b2_dynamicBody if dynamic else b2_kinematicBody
        body = self.world.CreateBody(
            type=body_type,
            position=(self.pixels_to_meters(x_px), self.pixels_to_meters(y_px)),
            bullet=bool(bullet),
            linearDamping=self.profile.linear_damping,
            angularDamping=self.profile.angular_damping,
            fixedRotation=False,
        )

        radius_m = max(0.05, self.pixels_to_meters(radius_px))
        fixture = body.CreateFixture(
            shape=b2CircleShape(radius=radius_m),
            density=max(0.001, float(mass)),
            friction=float(friction),
            restitution=float(restitution),
        )
        fixture.filterData = b2Filter(categoryBits=int(category), maskBits=int(mask), groupIndex=0)

        body.userData = entity
        self.entity_to_body[entity] = body
        return body

    def add_static_circle(
        self,
        entity,
        radius_px,
        category=CollisionCategory.METEOR,
        mask=0xFFFF,
        restitution=0.1,
        friction=0.4,
    ):
        x_px, y_px = self._entity_center(entity)
        body = self.world.CreateBody(
            type=b2_staticBody,
            position=(self.pixels_to_meters(x_px), self.pixels_to_meters(y_px)),
        )
        radius_m = max(0.05, self.pixels_to_meters(radius_px))
        fixture = body.CreateFixture(
            shape=b2CircleShape(radius=radius_m),
            density=1.0,
            friction=float(friction),
            restitution=float(restitution),
        )
        fixture.filterData = b2Filter(categoryBits=int(category), maskBits=int(mask), groupIndex=0)
        body.userData = entity
        self.entity_to_body[entity] = body
        return body

    def remove_entity(self, entity):
        body = self.entity_to_body.pop(entity, None)
        if body is not None:
            self.world.DestroyBody(body)

    def get_body(self, entity):
        return self.entity_to_body.get(entity)

    def step(self, dt_seconds):
        dt_seconds = max(0.0, float(dt_seconds))
        self.accumulator += dt_seconds

        self.contact_collector.reset_frame_metrics()
        substeps = 0
        t0 = time.perf_counter()

        while self.accumulator >= self.fixed_dt and substeps < self.max_substeps:
            self.world.Step(self.fixed_dt, self.velocity_iterations, self.position_iterations)
            self.world.ClearForces()
            self.accumulator -= self.fixed_dt
            substeps += 1

        alpha = self.accumulator / self.fixed_dt if self.fixed_dt > 0 else 0.0
        for entity, body in list(self.entity_to_body.items()):
            self._sync_entity_from_body(entity, body, alpha)

        self.step_time_ms = (time.perf_counter() - t0) * 1000.0
        self.last_substeps = substeps
        self.frame_contacts = self.contact_collector.begin_contacts

    def apply_explosion_impulse(self, center_px, radius_px, impulse_strength):
        center = pygame.Vector2(center_px)
        radius_px = max(1.0, float(radius_px))

        for body in self.entity_to_body.values():
            if body.type != b2_dynamicBody:
                continue

            pos_px = pygame.Vector2(
                self.meters_to_pixels(body.position.x),
                self.meters_to_pixels(body.position.y),
            )
            delta = pos_px - center
            dist = delta.length()
            if dist <= 1e-5 or dist > radius_px:
                continue

            direction = delta.normalize()
            falloff = max(0.0, 1.0 - (dist / radius_px))
            impulse = direction * (float(impulse_strength) * falloff)
            body.ApplyLinearImpulse(
                impulse=(self.pixels_to_meters(impulse.x), self.pixels_to_meters(impulse.y)),
                point=body.worldCenter,
                wake=True,
            )

    def get_metrics(self):
        return {
            "physics_step_ms": self.step_time_ms,
            "substeps": self.last_substeps,
            "contacts": self.frame_contacts,
            "profile": self.profile.name,
            "fixed_dt": self.fixed_dt,
        }

    @staticmethod
    def _entity_center(entity):
        try:
            if hasattr(entity, "pos"):
                p = pygame.Vector2(entity.pos)
                return p.x, p.y
        except Exception:
            pass

        rect = getattr(entity, "rect", None)
        if rect is not None:
            return float(rect.centerx), float(rect.centery)
        return 0.0, 0.0

    def _sync_entity_from_body(self, entity, body, alpha):
        x_px = self.meters_to_pixels(body.position.x)
        y_px = self.meters_to_pixels(body.position.y)
        vx_px = self.meters_to_pixels(body.linearVelocity.x)
        vy_px = self.meters_to_pixels(body.linearVelocity.y)

        try:
            entity.pos = pygame.Vector2(x_px, y_px)
        except Exception:
            pass

        try:
            entity.vel = pygame.Vector2(vx_px, vy_px)
        except Exception:
            pass

        try:
            entity.rect.center = (int(x_px), int(y_px))
        except Exception:
            pass

        try:
            entity.angle = -float(body.angle) * 57.29577951308232
        except Exception:
            pass
