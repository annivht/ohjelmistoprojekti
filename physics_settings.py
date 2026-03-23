import json
import os
from copy import deepcopy


SETTINGS_FILE = "physics_settings.json"
PRESETS_FILE = "physics_presets.json"

DEFAULT_PHYSICS_SETTINGS = {
    "sprite_angle_offset_deg": 0.0,
    "speed_multiplier": 1.35,
    "turn_multiplier": 0.7,
    "physics_profile": "balanced",
}


def _settings_path():
    return os.path.join(os.path.dirname(__file__), SETTINGS_FILE)


def _presets_path():
    return os.path.join(os.path.dirname(__file__), PRESETS_FILE)


def load_physics_settings():
    path = _settings_path()
    data = deepcopy(DEFAULT_PHYSICS_SETTINGS)

    try:
        with open(path, "r", encoding="utf-8") as fh:
            loaded = json.load(fh)
    except FileNotFoundError:
        return data
    except Exception:
        return data

    if not isinstance(loaded, dict):
        return data

    for key in DEFAULT_PHYSICS_SETTINGS:
        if key in loaded:
            data[key] = loaded[key]

    # Defensive normalization
    try:
        data["sprite_angle_offset_deg"] = float(data["sprite_angle_offset_deg"])
    except Exception:
        data["sprite_angle_offset_deg"] = 0.0

    try:
        data["speed_multiplier"] = float(data["speed_multiplier"])
    except Exception:
        data["speed_multiplier"] = 1.0

    try:
        data["turn_multiplier"] = float(data["turn_multiplier"])
    except Exception:
        data["turn_multiplier"] = 1.0

    profile = str(data.get("physics_profile", "balanced")).strip().lower()
    if profile not in {"realistic", "balanced", "arcade"}:
        profile = "balanced"
    data["physics_profile"] = profile

    data["speed_multiplier"] = max(0.3, min(3.5, data["speed_multiplier"]))
    data["turn_multiplier"] = max(0.3, min(3.5, data["turn_multiplier"]))
    data["sprite_angle_offset_deg"] = max(-180.0, min(180.0, data["sprite_angle_offset_deg"]))

    return data


def save_physics_settings(settings):
    path = _settings_path()
    data = deepcopy(DEFAULT_PHYSICS_SETTINGS)
    if isinstance(settings, dict):
        data.update(settings)

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def load_physics_presets():
    path = _presets_path()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}

    return data if isinstance(data, dict) else {}


def save_physics_preset(name, settings):
    preset_name = str(name).strip()
    if not preset_name:
        raise ValueError("Preset name cannot be empty")

    normalized = deepcopy(DEFAULT_PHYSICS_SETTINGS)
    if isinstance(settings, dict):
        normalized.update(settings)

    # Normalize with same limits as runtime settings.
    normalized = load_physics_settings() | {
        "sprite_angle_offset_deg": float(normalized.get("sprite_angle_offset_deg", 0.0)),
        "speed_multiplier": float(normalized.get("speed_multiplier", 1.0)),
        "turn_multiplier": float(normalized.get("turn_multiplier", 1.0)),
        "physics_profile": str(normalized.get("physics_profile", "balanced")).strip().lower(),
    }
    if normalized["physics_profile"] not in {"realistic", "balanced", "arcade"}:
        normalized["physics_profile"] = "balanced"
    normalized["speed_multiplier"] = max(0.3, min(3.5, normalized["speed_multiplier"]))
    normalized["turn_multiplier"] = max(0.3, min(3.5, normalized["turn_multiplier"]))
    normalized["sprite_angle_offset_deg"] = max(-180.0, min(180.0, normalized["sprite_angle_offset_deg"]))

    presets = load_physics_presets()
    presets[preset_name] = normalized

    with open(_presets_path(), "w", encoding="utf-8") as fh:
        json.dump(presets, fh, indent=2)


def get_physics_preset(name):
    preset_name = str(name).strip()
    if not preset_name:
        return None
    presets = load_physics_presets()
    preset = presets.get(preset_name)
    return preset if isinstance(preset, dict) else None
