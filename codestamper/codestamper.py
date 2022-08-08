import contextlib
import subprocess
import os
import platform
from datetime import datetime
import json
import sys

try:
    import pwd  # Used to get username if os.getlogin fails
except ImportError:
    pass

from typing import List, Union, Dict, Tuple


class GitNotFound(Exception):
    """Raised when git executable is not found"""


class DirtyWorkspace(Exception):
    """Git Workspace contains modified files and/or untracked files"""


class LastPushedCommitNA(Exception):
    """Cannot find a commit in history that is in sync with the git remote repo"""


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
    try:
        return platform.node()
    except Exception:
        return None


def pip_packages() -> Dict[str, str]:
    """Get pip packages & versions

    Returns
    -------
        Dictionary of python packages and versions
    """
    out = {}
    reqs = subprocess.check_output([sys.executable, "-m", "pip", "freeze"]).decode(
        "utf-8"
    )
    for line in reqs.splitlines():
        key, val = (line, None) if "==" not in line else line.split("==")
        out[key] = val
    return out


class GitStamp:
    def __init__(self, git_cmd: str = "git") -> None:
        self.git_cmd = git_cmd

    def _git(self, args: List[str], to_file: str = None):
        """Run a git command.

        Parameters
        ----------
        args
            Parameters to pass to git
        to_file, optional
            Write restuls to the file named to_file, by default None

        Returns
        -------
            The command result

        Raises
        ------
        GitNotFound
            If Git executable is not found
        """
        cmd = [self.git_cmd] + args
        try:
            if not to_file:
                return subprocess.check_output(cmd).decode("utf-8")
            with open(to_file, "w", encoding="utf-8") as fout:
                subprocess.run(cmd, stdout=fout, check=True)
                return None
        except FileNotFoundError as e:
            if e.filename == to_file:
                raise
            raise GitNotFound(
                f"Could not find git executable {e.filename} in system path"
                + "You can add it manually using GitStamp(git=/path/to/git)"
            ) from e

    def _git_config(self, param: str):
        """Return the value of the param argument from the git config

        Parameters
        ----------
        param
            Parameter name

        Returns
        -------
            Parameter value
        """
        return self._git(["config", "--get", param]).strip()

    def git_user_config(self):
        """Returns the username and email of the current git user"""
        usr = self._git_config("user.name")
        email = self._git_config("user.email")
        return usr, email

    def hash(self):
        """Returns the hash of the latest commit"""
        return self._git(["rev-parse", "--short", "HEAD"]).strip()

    def create_patch(self, out_fname: str):
        """Creates a git patch file containing the difference between the
            workspace and last commit

        Parameters
        ----------
        out_fname
            Name of the output file
        """
        patch = self._git(["diff", "HEAD"])
        with open(out_fname, "wt", encoding="utf-8") as f:
            f.write(patch)

    def modified(self) -> List[str]:
        """
        Returns
        -------
            A list of filenames which are modified from the last commit
        """
        return self._git(["ls-files", "-m"]).splitlines()

    def untracked(self, extensions: List[str] = None):
        """Returns a list of untracked files

        Parameters
        ----------
        extensions, optional
            List of targeted extensions. If None returns all untracked files, by default None

        Returns
        -------
            List of untracked fields
        """
        if isinstance(extensions, str):
            extensions = [extensions]
        fnames = self._git(["ls-files", "-o", "--exclude-standard"]).splitlines()
        if extensions:
            fnames = [
                el for el in fnames if any(el.endswith(ext) for ext in extensions)
            ]
        return fnames

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
            if num := self.modified():
                raise DirtyWorkspace(f"Encountered {num} modified files")
        if untracked:
            extensions = None if isinstance(untracked, bool) else untracked
            if num := self.untracked(extensions):
                raise DirtyWorkspace(f"Encountered {num} untracked files")

    def get_state_info(self, git_usr=True, node_info=True, python_info=True):
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
        state = {}
        state["date"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        git = state["git"] = {}
        git["hash"] = self.hash()
        if git_usr:
            git["user"], git["email"] = self.git_user_config()
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
        if python_info:
            py_info = state["python"] = {}
            py_info["version"] = sys.version

            py_info["pip_packages"] = pip_packages()
        return state

    def gen_mod_patch(self, folder, fname="mod.patch"):
        """Generate a diff(patch) between the workspace and the last commit."""
        os.makedirs(folder, exist_ok=True)
        if fname is None:
            fname = "mod.patch"
        self._git(["diff", "HEAD"], to_file=os.path.join(folder, fname))

    def get_unpushed_start_end(self) -> Tuple[str, str]:
        """Returns the hash of the last pushed commit & the last unpushed commit
        Raises
        ------
        LastPushedCommitNA
           Raises an error if no commits were pushed
        """
        push_marker = "refs/remotes/"
        lines = self._git(["reflog", "--all"]).splitlines()
        if push_marker in lines[0]:
            return None, None
        end = lines[0].split(" ", 1)[0]
        start = next(
            (line.split(" ", 1)[0] for line in lines[1:] if push_marker in line), None
        )

        if start is None:
            raise LastPushedCommitNA("Could not identify last pushed commit.")
        return start, end

    def gen_unpushed_patch(self, folder, fname=None):
        """Generate a diff(patch) between the last commit  and the last pushed commit."""
        os.makedirs(folder, exist_ok=True)
        start, end = self.get_unpushed_start_end()
        if fname is None:
            fname = f"unpushed{start}-{end}.patch"
        if start:
            self._git(["diff", start, end], to_file=os.path.join(folder, fname))

    def log_state(  # pylint: disable=R0913
        self,
        folder,
        modified_as_patch=True,
        unpushed_as_patch=False,
        git_usr=True,
        node_info=True,
        python_info=True,
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
        python_info, optional
            Save information related to python version & packages, by default True
        """
        os.makedirs(folder, exist_ok=True)
        info = self.get_state_info(git_usr, node_info, python_info)
        with open(os.path.join(folder, "code_state.json"), "wt", encoding="utf-8") as f:
            json.dump(info, f, indent=2)

        if modified_as_patch:
            self.gen_mod_patch(folder)

        if unpushed_as_patch:
            self.gen_unpushed_patch(folder)
