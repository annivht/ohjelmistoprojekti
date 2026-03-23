"""
Physics module - Unified physics engine for RocketGame

Provides:
- RigidBody: Base physics class for all entities
- Forces: Gravity, Drag, Magnetism, Thrust
- Animations: DampedOscillator for collision bounces
- Presets: Predefined physics profiles for enemy types
"""

from Physics.core import RigidBody
from Physics.forces import Force, Gravity, Drag, Magnetism, Thrust
from Physics.animation import DampedOscillator
from Physics.presets import ENEMY_PRESETS, create_enemy_physics
from Physics.box2d_config import PHYSICS_PROFILES, PhysicsProfile, get_physics_profile
from Physics.box2d_world import Box2DPhysicsWorld, CollisionCategory

__all__ = [
    'RigidBody',
    'Force',
    'Gravity',
    'Drag',
    'Magnetism',
    'Thrust',
    'DampedOscillator',
    'ENEMY_PRESETS',
    'create_enemy_physics',
    'PHYSICS_PROFILES',
    'PhysicsProfile',
    'get_physics_profile',
    'Box2DPhysicsWorld',
    'CollisionCategory',
]
