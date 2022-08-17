import pytest
import pathlib
import os
import subprocess
import shutil
from codestamper import GitStamp, GitNotFound, DirtyWorkspace, LastPushedCommitNA

# hash
# get_modified
# get_untracked
# raise_if


def run_cmd(cmd):
    return subprocess.check_output(cmd).decode("utf-8")


def get_commit_msg(hash):
    return run_cmd(["git", "log", "-1", '--pretty="%s"', hash]).strip()


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
    commit_id = stamp.git.get_hash()
    msg = get_commit_msg(commit_id)
    print(commit_id, msg)
    assert msg == '"c2"'

    assert len(stamp.git.modified()) == 0
    assert len(stamp.git.untracked()) == 1

    info = stamp.get_state_info()
    assert info["git"]["hash"] == commit_id

    with pytest.raises(DirtyWorkspace):
        stamp.raise_if_dirty()

    stamp.raise_if_dirty(untracked=False)

    stamp.log_state("./state")
    assert os.path.exists("./state/mod.patch")
    assert os.path.exists("./state/code_state.json")
    assert os.path.exists("./state/pip-packages.txt")
    assert not os.path.exists("./state/poetry.lock")

    with pytest.raises(LastPushedCommitNA):
        stamp.log_state("./state", unpushed_as_patch=True)

    poetry_fname = "poetry.lock"
    poetry_dst = os.path.join("./state2/", poetry_fname)

    pathlib.Path(poetry_fname).write_text("placeholder")

    GitStamp().log_state("./state2")
    assert os.path.exists(poetry_dst)
    assert pathlib.Path(poetry_dst).read_text() == "placeholder"
