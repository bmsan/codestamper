# CodeStamper

CodeStamper aims to help the user in ensuring traceability between ML experiments and code.

## Description
When running ML experiments one would want to be able to replicate a past experiment at any point in time. One aspect to achieve this(although not the only one) is to be able to run the exact same code version.

### When things go wrong. An ML experiment is started but it might not be  reproducible in the future because:
 - The experiment does not contain any information related to the code with which it was produced
 - Code modifications were staged but not commited
 - One modified file was missed when commiting
 - The code is commited, but the code never gets pushed 
 - The experiment does not contain exact information related to the python enviroment used. Even if all the code is versioned re-running the same experiment 8 months from now might not work the same if the python package versions have changed(APIs/implementations of different algorithms might have changed). 
 
CodeStamper to the rescue. It can:
- Log information related to last git commit
- Log any local changes not caught in a commit.
- Log contents of commits not already Pushed
- Log current python enviroment state
- Prevent running experiments before having all the local modifications versioned on git.

## Installing

```bash
pip install CodeStamper
```
## Examples

### Enforce a clean workspace
```py
from codestamper import Gitstamp

GitStamp().raise_if_dirty()
```

### Log the current code state
```py
from codestamper import Gitstamp

GitStamp().log_state('./experiment/code_log', modified_as_patch=True, unpushed_as_patch=True)
```
```
📁experiments/code_log
|--🗎 code_state.json
|--🗎 mod.patch
|--🗎 unpushed<git-commit>-<git-commit>.patch
```
- code_state.json
```json
{
  "date": "03/08/2022 21:10:34",
  "git": {
    "hash": "75c88ba",
    "user": "git-usernmae",
    "email": "your-email-here@gmail.com"
  },
  "node": {
    "username": "gitpod",
    "node": "bmsan-gitstamp",
    "system": "Linux",
    "version": "#44-Ubuntu SMP Wed Jun 22 14:20:53 UTC 2022",
    "release": "5.15.0-41-generic"
  },
  "python": {
    "version": "3.8.13 (default, Jul 26 2022, 01:36:30) \n[GCC 9.4.0]",
    "pip_packages": {
      "argon2-cffi": "21.3.0",
      "argon2-cffi-bindings": "21.2.0",
        .....
    }
  }
}
```

- `mod.patch`

Contains modifications(staged/or unstaged) of git tracked files

The modifications can be applied in an workspace over the commit hash mentioned in the `code_state.json`
```bash
# Make sure we are at the right commit
git checkout <git.hash from code_state.json>

# Add uncommited changes to the workspace
git apply mod.patch
```

- `unpushed<last_pushed_commit_hash>-<last_unpushed_commit_hash>.patch`

Contains the delta between the current commit and last pushed commit.
This should be used only in the unlikely event when the unpushed commits get lost.
It should be considered an experimental last resort feature.


```bash
# Make sure we are at the right commit
git checkout <last_pushed_commit_hash>

# Add uncommited changes to the workspace
git apply unpushed<last_pushed_commit_hash>-<last_unpushed_commit_hash>.patch
```

