import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "panel_id": "",
    "language": "English",
    "minimize_to_tray": True,
    "panel_password": "",
    "error_sound_type": "Default (Beep)",
    "theme": "Discord Dark (Default)",
    "log_save_level": "Save everything",
    "max_ram_mb": 200,
    "task_kill_enabled": False,
    "rpc_enabled": True
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Alapértelmezett értékek kiegészítése, ha hiányoznának
                for key, val in DEFAULT_SETTINGS.items():
                    if key not in data:
                        data[key] = val
                return data
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings_dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings_dict, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Hiba a beállítások mentésekor: {e}")