import json
import os
from threading import Lock
from .Logger import Logger
from .Utils import store_json_on_disk, load_json_from_disk

class ConfigManager:
    _instance = None
    _lock = Lock()    
    
    def __new__(cls, config_file_path="Data/config.json"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance._init(config_file_path)
        return cls._instance

    def _init(self, config_file_path):
        self.config_file_path = config_file_path
        self._lock = Lock()
        self.logger = Logger()
        # Load or create an empty config
        if not os.path.exists(self.config_file_path):
            store_json_on_disk({}, self.config_file_path, "Empty Config")            
        self._load_config()

    def _load_config(self):
        with self._lock:
            try:
                self.config = load_json_from_disk(self.config_file_path, "Config")                
            except json.JSONDecodeError:
                self.config = {}  # Reset to empty config if corrupted

    def _save_config(self):
        with self._lock:
            store_json_on_disk(self.config, self.config_file_path, "Config")            

    def read(self, key):
        """Reads a value from the config by key. Returns an empty string if key doesn't exist."""
        configvalue = self.config.get(key, "")
        self.logger.LogMessage(f"Reading config: {key} = {configvalue}", self)        
        return configvalue

    def write(self, key, value):
        """Writes a value to the config. Creates the key if it doesn't exist."""        
        self.config[key] = value
        self._save_config()
        self.logger.LogMessage(f"Config updated: {key} = {value}", self)

# Usage Example
# if __name__ == "__main__":
#     # Ensure singleton behavior
#     config = ConfigManager()
#     config.write("username", "admin")
#     print(config.read("username"))  # Outputs: admin
#     print(config.read("non_existent_key"))  # Outputs: (empty string)

#     # Another instance of the singleton points to the same object
#     config2 = ConfigManager()
#     print(config2.read("username"))  # Outputs: admin
