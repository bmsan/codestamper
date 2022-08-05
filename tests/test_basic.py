import pytest
from gitstamp import GitStamp, GitNotFound
import os
import subprocess
import shutil

# hash
# get_modified
# get_untracked
# raise_if


def run_cmd(cmd):
    return subprocess.check_output(cmd).decode("utf-8")


def get_commit_msg(hash):
    return run_cmd(["git", "log", "-1", '--pretty="%s"', hash]).strip()
    # git log --pretty=format":%s" 93f41f90daba6ee31907d5f83eb52bd3bf3ee7c9


def test_git_not_found():
    stamp = GitStamp(git_cmd="/usr/not/found/git")
    with pytest.raises(GitNotFound):
        stamp.raise_if_dirty()


def test_A():
    print("A", os.getcwd())


def git_init(monkeypatch, folder):
    os.makedirs(folder, exist_ok=True)
    monkeypatch.chdir(folder)
    run_cmd("../../git_init.sh")
    yield
    folder = os.path.basename(folder)
    monkeypatch.chdir("..")
    shutil.rmtree(folder)


@pytest.fixture
def git_env1(monkeypatch: pytest.MonkeyPatch):
    yield from git_init(monkeypatch, "./tests/tmp/git_env")


def test_B(git_env1):
    stamp = GitStamp()
    commit_id = stamp.hash()
    msg = get_commit_msg(commit_id)
    print(commit_id, msg)
    assert msg == '"c2"'
