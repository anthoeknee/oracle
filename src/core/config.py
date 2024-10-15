import toml
from types import SimpleNamespace
from src.utils.monitor import Monitor

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        self.monitor = Monitor(__name__)
        try:
            config_dict = toml.load('settings.toml')
            self.config = self._dict_to_namespace(config_dict)
            self.monitor.log_info("Configuration loaded successfully")
        except Exception as e:
            self.monitor.log_error(f"Error loading configuration: {e}")
            raise

    def _dict_to_namespace(self, d):
        """Recursively convert a dictionary to a SimpleNamespace."""
        for key, value in d.items():
            if isinstance(value, dict):
                d[key] = self._dict_to_namespace(value)
        return SimpleNamespace(**d)

    def __getattr__(self, item):
        return getattr(self.config, item)

# Create a single instance of Config
config = Config()

# Example usage
# print(config['database']['url'])  # Accessing a config value using dictionary notation
# print(config.database.url)  # Accessing a config value using dot notation
