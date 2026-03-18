import yaml
from pathlib import Path


class ProfileLoader:

    def __init__(self, profile_name):

        profile_path = Path("icaf/profile") / f"{profile_name}.yaml"

        if not profile_path.exists():
            raise FileNotFoundError(f"Profile {profile_name} not found")

        with open(profile_path) as f:
            self.data = yaml.safe_load(f)

    def get(self, key, default=None):

        keys = key.split(".")

        value = self.data

        for k in keys:
            value = value.get(k, {})

        return value or default