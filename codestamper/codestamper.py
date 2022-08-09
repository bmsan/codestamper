import contextlib
import subprocess
import os
import platform
from datetime import datetime
import json
import sys
from .gitutils import Git, GitNotFound, LastPushedCommitNA

try:
    import pwd  # Used to get username if os.getlogin fails
except ImportError:
    pass

from typing import List, Union, Tuple
from .pythonenv import PipEnv, CondaEnv


class DirtyWorkspace(Exception):
    """Git Workspace contains modified files and/or untracked files"""


def get_username():
    """
    Returns
    -------
        The system username of the current user
    """
    with contextlib.suppress(Exception):
        return os.getlogin()
    with contextlib.suppress(Exception):
        return pwd.getpwuid(os.getuid())[0]
    return None


def get_hostname():
    """Retrivies node hostname"""
    try:
        return platform.node()
    except Exception:
        return None


class GitStamp:
    """Provides ways of logging & retriving data related to Workspace state & python env"""

    def __init__(self, git_cmd: str = "git") -> None:
        self.git = Git(git_cmd)
        self.pip = PipEnv()
        self.conda = CondaEnv()

    def raise_if_dirty(
        self, modified: bool = True, untracked: Union[bool, List[str]] = True
    ):
        """Raise DirtyWorkspace exception if git workspace is dirty

        Parameters
        ----------
        modified, optional
            check for modified but uncommited files, by default True

        untracked, optional
            check for untracked git files.
            it can receive a list of targeted file extensions which can be given to it,
            by default True

        Raises
        ------
        DirtyWorkspace

        """
        if modified:
            if num := self.git.modified():
                raise DirtyWorkspace(f"Encountered {num} modified files")
        if untracked:
            extensions = None if isinstance(untracked, bool) else untracked
            if num := self.git.untracked(extensions):
                raise DirtyWorkspace(f"Encountered {num} untracked files")

    def get_state_info(
        self, git_usr=True, node_info=True, pip_info=True, conda_info=True
    ):
        """Returns information related to:
          - git state
          - node(machine) state
          - python env

        Parameters
        ----------
        git_usr, optional
            Include information related to the current git user, by default True
        node_info, optional
            Include information related to the current machine, by default True
        python_info, optional
            Include information related to the python env, by default True

        """
        state = {"date": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
        git = state["git"] = {}
        git["hash"] = self.git.get_hash()
        if git_usr:
            git["user"], git["email"] = self.git.git_user_config()
        if node_info:
            node = state["node"] = {}
            node["username"] = get_username()
            uname = platform.uname()
            for key in ["node", "system", "version", "release"]:
                try:
                    val = getattr(uname, key)
                except AttributeError():
                    val = None
                node[key] = val

        py_info = state["python"] = {}
        py_info["version"] = sys.version

        if pip_info:
            py_info["pip_packages"] = self.pip.get_env_info()
        if conda_info and self.conda.activated:
            py_info["conda"] = self.conda.get_env_info()

        return state

    def log_state(  # pylint: disable=R0913
        self,
        folder,
        modified_as_patch=True,
        unpushed_as_patch=False,
        git_usr=True,
        node_info=True,
        pip_info=True,
        conda_info=True,
    ):
        """Logs Code & Env State.
        Generates a folder containing logged information.
          - code_state.json - contains git/platform/python information
          - mod.patch - contains diff between last commit and current code
          - unpatched<>-<>.patch - contains diff between last commit and last pushed commit

        Parameters
        ----------
        folder
            Folder where the state is logged
        modified_as_patch, optional
            Save code modifications(since last commit) as a patch file [mod.patch], by default True
        unpushed_as_patch, optional
            Save code modifications of unpushed commits as patch file
            [unpushed<hash1>-<hash2>.patch], by default False
        git_usr, optional
            Save git info related to current git user, by default True
        node_info, optional
            Save information related to the machine that the code is running on, by default True
        pip_info, optional
            Information related to python packages gathered through pip, by default True
        conda_info, optional
            Information related to python packages in conda envs, by default True
        """
        os.makedirs(folder, exist_ok=True)
        info = self.get_state_info(git_usr, node_info, pip_info, conda_info)
        with open(os.path.join(folder, "code_state.json"), "wt", encoding="utf-8") as f:
            json.dump(info, f, indent=2)

        if modified_as_patch:
            self.git.gen_mod_diff(folder)

        if unpushed_as_patch:
            self.git.gen_unpushed_diff(folder)

        if pip_info:
            self.pip.save_raw(os.path.join(folder, "pip-packages.txt"))
        if conda_info and self.conda.activated:
            self.conda.save_raw(os.path.join(folder, "conda_env.yaml"))
