from typing import Dict, List

# instead of relying on enviroment varibles loaded at runtime in individual functions
# we'll load a config dict and DI it into everything. 

# TODO ideally we'd load everything into the env before the application starts
# and just load a static config with known properties. But this will do for now
# https://12factor.net/config REF FOR BEST PRACTICE

def config_factory(config_paths: List[str] = ["prompt-eng/config.cfg"]) -> Dict[str, str]:
    required_keys = ["chatbot_api_host", "bearer"]
    config = {}
    for path in config_paths:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split('=', 1)
                    config[key.strip().lower()] = value.strip()
    
    # Add validation
    missing = [key for key in required_keys if key not in config]
    if missing:
        raise ValueError(f"Missing required config keys: {', '.join(missing)}")
    return config




