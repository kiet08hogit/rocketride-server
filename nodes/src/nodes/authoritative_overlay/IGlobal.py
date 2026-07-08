from rocketlib import IGlobalBase, debug, warning
import json

class IGlobal(IGlobalBase):
    def __init__(self):
        super().__init__()
        self.regulator_type = 'sec'

    def initialize(self):
        """Initialize the global authoritative overlay configuration."""
        # Read the profile from the JSON configuration
        profile = self.getProperty('authoritative_overlay.profile')
        if not profile:
            warning("No profile specified for authoritative overlay. Defaulting to basic.")
            profile = "basic"

        config_prop = f"authoritative_overlay.{profile}"
        config = self.getProperty(config_prop)

        if config:
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except Exception as e:
                    warning(f"Failed to parse overlay config JSON: {e}")
                    config = {}

            self.regulator_type = config.get('regulator_type', 'sec')
        else:
            warning(f"Could not find configuration for profile '{profile}'. Using defaults.")
            self.regulator_type = 'sec'

        debug(f"Initialized Authoritative Overlay with regulator: {self.regulator_type}")
        return True

    def terminate(self):
        """Clean up resources on shutdown."""
        pass
