import json
import os
from typing import Dict, Tuple

CONFIG_FILE = 'config.json'


class ConfigService:
    """
    Dedicated domain service managing configuration persistence (config.json).
    Thread-safe and decoupled from Flask request lifecycles.
    """

    @classmethod
    def get_config_path(cls) -> str:
        return os.path.abspath(CONFIG_FILE)

    @classmethod
    def load_config(cls) -> Dict[str, str]:
        """
        Loads the persistent configuration dictionary.
        Returns a dictionary with 'image_folder', 'video_folder', and 'performance_profile' keys.
        """
        if not os.path.exists(CONFIG_FILE):
            return {'image_folder': '', 'video_folder': '', 'performance_profile': 'max_speed'}
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    'image_folder': data.get('image_folder', '').strip(),
                    'video_folder': data.get('video_folder', '').strip(),
                    'performance_profile': data.get('performance_profile', 'max_speed').strip()
                }
        except Exception:
            return {'image_folder': '', 'video_folder': '', 'performance_profile': 'max_speed'}

    @classmethod
    def save_config(cls, image_folder: str, video_folder: str, performance_profile: Optional[str] = None) -> None:
        """
        Persists image_folder, video_folder, and performance_profile into config.json.
        """
        current = cls.load_config()
        cfg = {
            'image_folder': image_folder.strip(),
            'video_folder': video_folder.strip(),
            'performance_profile': (performance_profile or current.get('performance_profile') or 'max_speed').strip()
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=4)

    @classmethod
    def get_performance_profile(cls) -> str:
        """
        Returns the active performance profile ('max_speed' or 'balanced').
        """
        return cls.load_config().get('performance_profile', 'max_speed')

    @classmethod
    def set_performance_profile(cls, profile: str) -> None:
        """
        Updates the performance profile in config.json.
        """
        cfg = cls.load_config()
        cls.save_config(cfg.get('image_folder', ''), cfg.get('video_folder', ''), performance_profile=profile)

    @classmethod
    def get_configured_folders(cls) -> Tuple[str, str]:
        """
        Convenience accessor returning (image_folder, video_folder).
        """
        cfg = cls.load_config()
        return cfg.get('image_folder', ''), cfg.get('video_folder', '')

