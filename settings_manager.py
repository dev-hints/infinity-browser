import os
import json

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')

class SettingsManager:
    def __init__(self):
        self.default_settings = {
            # General
            "search_engine": "Google",
            "search_urls": {
                "Google":     "https://www.google.com/search?q={}",
                "DuckDuckGo": "https://duckduckgo.com/?q={}",
                "Bing":       "https://www.bing.com/search?q={}",
                "Ecosia":     "https://www.ecosia.org/search?q={}",
                "Brave":      "https://search.brave.com/search?q={}",
            },
            "homepage_url": "new_tab.html",
            "show_home_btn": True,
            "restore_tabs":  False,

            # Appearance
            "ui_theme":      "dark",    # fixed app chrome theme: dark/light
            "font_size":     16,       # px, applied via WebEngine settings
            "default_zoom":  100,      # percent

            # Privacy & Security
            "adblock_enabled":   True,
            "do_not_track":      True,
            "block_popups":      True,
            "javascript_enabled": True,
            "https_only":        False,
            "safe_browsing":     True,

            # Downloads
            "download_mode": "ask",
            "download_dir":  os.path.join(os.path.expanduser("~"), "Downloads"),
        }
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                # Merge with defaults so new keys always exist
                for k, v in self.default_settings.items():
                    if k not in data:
                        data[k] = v
                # Always keep full search_urls dict
                data["search_urls"] = self.default_settings["search_urls"]
                return data
            except Exception:
                pass
        return self.default_settings.copy()

    def save_settings(self):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key, default=None):
        return self.settings.get(key, default if default is not None else self.default_settings.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

    def get_search_url(self, query):
        engine = self.get("search_engine")
        template = self.settings["search_urls"].get(engine, self.settings["search_urls"]["Google"])
        return template.format(query)
