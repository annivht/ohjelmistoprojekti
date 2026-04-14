"""
PyInstaller build script for RocketGame - onefile version with icon
"""

import os
import subprocess
import sys
from pathlib import Path


def build_executable():
    """Rakentaa pelistä suoritettavan yksittaisen .exe-tiedoston"""
    
    project_root = Path(__file__).parent
    icon_path = project_root / "build" / "game_icon.ico"
    
    print("[BUILD] Starting RocketGame executable build (onefile)...")
    print(f"[PATH] {project_root}\n")
    
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=RocketGame",
        "--onefile",
        "--windowed",
        f"--icon={icon_path}",
        "--hidden-import=pygame",
        "--hidden-import=pygame_menu",
        "--hidden-import=Box2D",
        "--hidden-import=Box2D._Box2D",
        "--hidden-import=json",
        "--hidden-import=pathlib",
        f"--add-data={project_root / 'Aanet'}{os.pathsep}Aanet",
        f"--add-data={project_root / 'Valikot'}{os.pathsep}Valikot",
        f"--add-data={project_root / 'images'}{os.pathsep}images",
        f"--add-data={project_root / 'alukset'}{os.pathsep}alukset",
        f"--add-data={project_root / 'Audio'}{os.pathsep}Audio",
        f"--add-data={project_root / 'Collision'}{os.pathsep}Collision",
        f"--add-data={project_root / 'Enemies'}{os.pathsep}Enemies",
        f"--add-data={project_root / 'Hazards'}{os.pathsep}Hazards",
        f"--add-data={project_root / 'Meteor'}{os.pathsep}Meteor",
        f"--add-data={project_root / 'Physics'}{os.pathsep}Physics",
        f"--add-data={project_root / 'PLAYER_LUOKAT'}{os.pathsep}PLAYER_LUOKAT",
        f"--add-data={project_root / 'States'}{os.pathsep}States",
        f"--add-data={project_root / 'Tasot'}{os.pathsep}Tasot",
        f"--add-data={project_root / 'SETTINGS-tiedostot'}{os.pathsep}SETTINGS-tiedostot",
        "--collect-all=pygame",
        "--collect-all=pygame_menu",
        "--collect-all=Box2D",
        f"--distpath={project_root / 'build' / 'dist'}",
        f"--workpath={project_root / 'build' / 'build_temp'}",
        f"--specpath={project_root / 'build'}",
        "-y",
        str(project_root / "main.py")
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    
    if result.returncode == 0:
        exe_path = project_root / "build" / "dist" / "RocketGame.exe"
        print(f"\n[SUCCESS] Build complete!")
        print(f"[LOCATION] {exe_path}")
        if exe_path.exists():
            print(f"[SIZE] {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        print(f"[RUN] Double-click RocketGame.exe to start")
        return True
    else:
        print(f"\n[ERROR] Build failed with code {result.returncode}")
        return False


if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)
