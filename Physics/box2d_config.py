from dataclasses import dataclass


@dataclass(frozen=True)
class PhysicsProfile:
    name: str
    linear_damping: float
    angular_damping: float
    thrust_force: float
    turn_torque: float
    max_speed_mps: float
    brake_impulse: float
    lateral_drift_damping: float


PHYSICS_PROFILES = {
    "realistic": PhysicsProfile(
        name="realistic",
        linear_damping=0.28,
        angular_damping=1.6,
        thrust_force=22.0,
        turn_torque=7.2,
        max_speed_mps=18.0,
        brake_impulse=2.2,
        lateral_drift_damping=2.4,
    ),
    "balanced": PhysicsProfile(
        name="balanced",
        linear_damping=0.22,
        angular_damping=1.35,
        thrust_force=34.0,
        turn_torque=10.4,
        max_speed_mps=26.0,
        brake_impulse=3.6,
        lateral_drift_damping=3.1,
    ),
    "arcade": PhysicsProfile(
        name="arcade",
        linear_damping=0.16,
        angular_damping=1.05,
        thrust_force=48.0,
        turn_torque=13.8,
        max_speed_mps=34.0,
        brake_impulse=4.9,
        lateral_drift_damping=4.1,
    ),
}


def get_physics_profile(name="balanced"):
    return PHYSICS_PROFILES.get(name, PHYSICS_PROFILES["balanced"])
