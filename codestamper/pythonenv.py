import os
import pathlib
import sys
import subprocess
from abc import ABC, abstractmethod
import yaml


class Env(ABC):
    """Base Class for python Enviroment extractors."""

    def __init__(self):
        self.raw = ""
        self.parsed = {}
        self._loaded = False
        self.active = False

    @abstractmethod
    def load_env(self):
        """Extract env information"""
        if self._loaded:
            return
        self._loaded = True

    def save_raw(self, fname):
        """Save env information to file"""
        self.load_env()
        with open(fname, "wt", encoding="utf-8") as f:
            f.write(self.raw)

    def get_env_info(self) -> dict:
        """Get env information"""
        self.load_env()
        return self.parsed


class CondaEnv(Env):
    """Retrives Conda package information"""

    def __init__(self) -> None:
        super().__init__()
        self.activated = os.environ.get("CONDA_PREFIX", None) is not None
        self.pip_deps = None
        self.conda_deps = None

    def load_env(self):
        super().load_env()
        if not self.activated:
            return
        cmd = ["conda", "env", "export"]
        try:
            data = subprocess.check_output(cmd).decode("utf-8")
        except FileNotFoundError:
            # On Windows conda command is seen only for shell=True
            data = subprocess.check_output(' '.join(cmd), shell=True).decode("utf-8")
        self.raw = data
        self.parsed = yaml.safe_load(data)
        self._interpret_deps(self.parsed["dependencies"])

    def _interpret_deps(self, data):
        conda_deps = {}
        pip_deps = {}
        for item in data:
            if isinstance(item, str):
                name, version, build = item.split("=")
                conda_deps[name] = {"version": version, "build": build}
            elif isinstance(item, dict):
                if list(item.keys())[0] == "pip":
                    for val in list(item.values())[0]:
                        tokens = val.split("==")
                        if len(tokens) == 2:
                            pip_deps[tokens[0]] = tokens[1]
                        else:
                            pip_deps[val] = None
        self.conda_deps = conda_deps
        self.pip_deps = pip_deps

    def get_env_info(self):
        self.load_env()
        return (
            {
                "name": self.parsed["name"],
                "prefix": self.parsed["prefix"],
                "channels": self.parsed["channels"],
                "dependencies": {"conda": self.conda_deps, "pip": self.pip_deps},
            }
            if self.activated
            else None
        )


class PoetryEnv(Env):
    """Retrives Poetry package information"""

    ENV_FILE = "poetry.lock"

    def __init__(self) -> None:
        super().__init__()
        self.activated = os.path.exists(PoetryEnv.ENV_FILE)
        self.raw = ""

    def load_env(self):
        super().load_env()
        if not self.activated:
            return
        self.raw = pathlib.Path(PoetryEnv.ENV_FILE).read_text(encoding="utf-8")

    def get_env_info(self):
        return {"present": self.activated}


class PipEnv(Env):
    """Retrives python package information from PIP"""

    def load_env(self):
        super().load_env()
        self.raw = subprocess.check_output(
            [sys.executable, "-m", "pip", "freeze"]
        ).decode("utf-8")

        self.parsed = {}
        for line in self.raw.splitlines():
            key, val = (line, None) if "==" not in line else line.split("==")
            self.parsed[key] = val
