import os
import subprocess
from typing import List, Tuple


class GitNotFound(Exception):
    """Raised when git executable is not found"""


class LastPushedCommitNA(Exception):
    """Cannot find a commit in history that is in sync with the git remote repo"""


class Git:
    """Provides git information"""

    def __init__(self, git_cmd: str = "git") -> None:
        self.git_cmd = git_cmd

    def cmd(self, args: List[str], to_file: str = None):
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

    def get_config(self, param: str):
        """Return the value of the param argument from the git config

        Parameters
        ----------
        param
            Parameter name

        Returns
        -------
            Parameter value
        """
        return self.cmd(["config", "--get", param]).strip()

    def git_user_config(self):
        """Returns the username and email of the current git user"""
        usr = self.get_config("user.name")
        email = self.get_config("user.email")
        return usr, email

    def get_hash(self):
        """Returns the hash of the latest commit"""
        return self.cmd(["rev-parse", "--short", "HEAD"]).strip()

    def modified(self) -> List[str]:
        """
        Returns
        -------
            A list of filenames which are modified from the last commit
        """
        return self.cmd(["ls-files", "-m"]).splitlines()

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
        fnames = self.cmd(["ls-files", "-o", "--exclude-standard"]).splitlines()
        if extensions:
            fnames = [
                el for el in fnames if any(el.endswith(ext) for ext in extensions)
            ]
        return fnames

    def gen_mod_diff(self, out_folder=None, fname=None):
        """Generate a diff(patch) between the workspace and the last commit."""
        to_file = None
        if out_folder:
            os.makedirs(out_folder, exist_ok=True)
            if fname is None:
                fname = "mod.patch"
            to_file = os.path.join(out_folder, fname)
        return self.cmd(["diff", "HEAD"], to_file=to_file)

    def gen_unpushed_diff(self, out_folder=None, fname=None):
        """Generate a diff(patch) between the last commit  and the last pushed commit."""
        start, end = self.get_unpushed_start_end()
        to_file = None
        if out_folder:
            os.makedirs(out_folder, exist_ok=True)
            if fname is None:
                fname = f"unpushed{start}-{end}.patch"
            to_file = os.path.join(out_folder, fname)

        return self.cmd(["diff", start, end], to_file=to_file) if start else None

    def get_unpushed_start_end(self) -> Tuple[str, str]:
        """Returns the hash of the last pushed commit & the last unpushed commit
        Raises
        ------
        LastPushedCommitNA
           Raises an error if no commits were pushed
        """
        push_marker = "refs/remotes/"
        lines = self.cmd(["reflog", "--all"]).splitlines()
        if push_marker in lines[0]:
            return None, None
        end = lines[0].split(" ", 1)[0]
        start = next(
            (line.split(" ", 1)[0] for line in lines[1:] if push_marker in line), None
        )

        if start is None:
            raise LastPushedCommitNA("Could not identify last pushed commit.")
        return start, end
