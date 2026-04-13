"""
Test script to simulate StraightEnemy motion without game loop.
Prints debug info frame-by-frame to identify motion issues.
"""

import pygame
import sys
import os

# Setup path to project root when running from Tests folder
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from Enemies.EnemyAI import StraightEnemy
except Exception as exc:
    print("StraightEnemy test skipped: Box2D dependency is not available.")
    print(f"Reason: {exc}")
    raise SystemExit(0)

# Initialize pygame without display
pygame.init()
pygame.display.set_mode((1, 1))

# Create dummy image
dummy_img = pygame.Surface((32, 32))
dummy_img.fill((255, 0, 0))

# Create world rect (game boundaries)
world_rect = pygame.Rect(0, 0, 800, 600)

# Create StraightEnemy near the edge
enemy = StraightEnemy(dummy_img, x=100, y=300, speed=220, path_type='random')

print("=" * 80)
print("STRAIGHTENEMY MOTION DEBUG TEST")
print("=" * 80)
print(f"\nWorld boundaries: {world_rect}")
print(f"Enemy initial position: ({enemy.pos.x:.1f}, {enemy.pos.y:.1f})")
print(f"Enemy initial velocity: ({enemy.vel.x:.1f}, {enemy.vel.y:.1f})")
print(f"Enemy speed: {enemy.speed}")
print(f"Magnet enabled: {getattr(enemy, 'magnet_enabled', False)}")
print(f"Random motion: {getattr(enemy, 'random_motion', False)}")
print("\n" + "=" * 80)

# Simulate frames
dt_ms = 16  # ~60 FPS
max_frames = 300  # 5 seconds of simulation
frame_count = 0
wall_collision_frame = None

print(f"\nSimulating {max_frames} frames (dt_ms={dt_ms}):\n")
print("Frame | Time(s) | Pos(X,Y)         | Vel(X,Y)         | Oscillator Status          | Notes")
print("-" * 120)

for frame in range(max_frames):
    frame_count += 1
    time_s = frame * dt_ms / 1000.0
    
    # Store old position to track movement
    old_pos = pygame.Vector2(enemy.pos)
    
    # Update enemy
    enemy.update(dt_ms, player=None, world_rect=world_rect)
    
    # Calculate movement delta
    delta_pos = enemy.pos - old_pos
    movement = delta_pos.length()
    
    # Check oscillator status
    osc_status = "INACTIVE"
    osc_info = ""
    if enemy.oscillator is not None:
        if enemy.oscillator.is_active():
            osc_status = f"ACTIVE({enemy.oscillator.timer:.2f}s)"
        else:
            osc_status = "FINISHED (should be None next frame)"
    
    # Check for wall collision
    wall_collision = ""
    if (enemy.rect.left <= world_rect.left or 
        enemy.rect.right >= world_rect.right or
        enemy.rect.top <= world_rect.top or
        enemy.rect.bottom >= world_rect.bottom):
        if wall_collision_frame is None:
            wall_collision_frame = frame
        wall_collision = " ⚠️ AT WALL"
    
    # Print debug info every frame for first 100 frames or when something interesting happens
    should_print = (frame < 100 or 
                   movement < 1.0 or  # Stuck?
                   enemy.oscillator is not None or  # Oscillating?
                   wall_collision or  # At wall?
                   frame % 10 == 0)  # Every 10 frames after frame 100
    
    if should_print:
        print(f"{frame:3d}  | {time_s:6.2f}s | "
              f"({enemy.pos.x:7.1f},{enemy.pos.y:6.1f}) | "
              f"({enemy.vel.x:8.1f},{enemy.vel.y:7.1f}) | "
              f"{osc_status:26s} | "
              f"Move={movement:5.1f}{wall_collision}")

print("\n" + "=" * 80)
print(f"Simulation complete: {frame_count} frames ({frame_count * dt_ms / 1000.0:.2f} seconds)")
print(f"Final position: ({enemy.pos.x:.1f}, {enemy.pos.y:.1f})")
print(f"Final velocity: ({enemy.vel.x:.1f}, {enemy.vel.y:.1f})")
print(f"Wall collision occurred at frame: {wall_collision_frame if wall_collision_frame else 'Never'}")

# Analysis
print("\n" + "=" * 80)
print("ANALYSIS:")
print("=" * 80)

if enemy.oscillator is not None and enemy.oscillator.is_active():
    print("❌ WARNING: Oscillator still active at end of simulation!")
    print(f"   Remaining time: {enemy.oscillator.timer:.2f}s")

if wall_collision_frame is not None:
    print(f"✓ Wall collision detected at frame {wall_collision_frame} ({wall_collision_frame * dt_ms / 1000.0:.2f}s)")
    
    # Check if movement became very slow or stuck
    final_speed = enemy.vel.length()
    if final_speed < 10:
        print(f"❌ WARNING: Final velocity very low ({final_speed:.1f} px/s)")
        print("   Enemy may be stuck or moving too slowly")
    elif final_speed < enemy.speed * 0.5:
        print(f"⚠️  Final velocity reduced ({final_speed:.1f} px/s vs expected {enemy.speed} px/s)")
else:
    print("⚠️  No wall collision in 300 frames - enemy may not be moving toward walls")

print("\n" + "=" * 80)
