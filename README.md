# CodeStamper

![](https://raw.githubusercontent.com/bmsan/codestamper/main/docs/source/CodeStamper.png)

[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=bmsan_codestamper&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=bmsan_codestamper)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=bmsan_codestamper&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=bmsan_codestamper)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=bmsan_codestamper&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=bmsan_codestamper)
[![Code Coverage](https://codecov.io/gh/bmsan/codestamper/branch/main/graph/badge.svg?token=0UPE6C3S7W)](https://codecov.io/gh/bmsan/codestamper)
[![CI status](https://github.com/bmsan/codestamper/workflows/CI/badge.svg)](https://github.com/bmsan/codestamper/actions?queryworkflow%3ACI+event%3Apush+branch%3Amain)
[![Docs](https://readthedocs.org/projects/codestamper/badge/?version=latest)](https://readthedocs.org/projects/codestamper)
![Pylint](https://img.shields.io/badge/Pylint->=9.90/10-green)



CodeStamper aims to help the user in ensuring traceability between ML experiments and code.



## 1.1. Description
When running ML experiments one would want to be able to replicate a past experiment at any point in time. One aspect to achieve this(although not the only one) is to be able to run the exact same code version.

### 1.1.1. When things go wrong. An ML experiment is started but it might not be  reproducible in the future because:

| Issue                                                                                                                                                                                                                                                                                                                   | CodeStamper's solution                                                                                                                                                              |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The experiment does not contain any information related to the code with which it was produced                                                                                                                                                                                                                          | ✅ Logs information related to last git commit                                                                                                                                       |
| Code modifications were staged but not commited or not all modified files were commited                                                                                                                                                                                                                                 | ✅ Logs any local changes not caught in a commit as patches that can be restored. <br> ✅ Can prevent running experiments before having all the local modifications versioned on git. |
| The code is commited, but the code never gets pushed                                                                                                                                                                                                                                                                    | ✅Can log contents of commits not already Pushed                                                                                                                                     |
| The experiment does not contain exact information related to the python enviroment used.  <br> Even if all the code is versioned re-running the same experiment 8 months from now might not work the same if the python package versions have changed(APIs/implementations of different algorithms might have changed). | ✅ Logs current python environment state                                                                                                                                             |
|                                                                                                                                                                                                                                                                                                                         |                                                                                                                                                                                     |

## 1.2. Installing

```bash
pip install codestamper
```
## 1.3. Examples

### 1.3.1. Enforce a clean workspace
```py
from codestamper import Gitstamp

GitStamp().raise_if_dirty()
```

### 1.3.2. Log the current code state
```py
from codestamper import Gitstamp

GitStamp().log_state('./experiment/code_log', modified_as_patch=True, unpushed_as_patch=True)
```
```
📁experiments/code_log
|--🗎 code_state.json
|--🗎 mod.patch
|--🗎 unpushed<git-commit>-<git-commit>.patch
|--🗎 pip-packages.txt
|--🗎 conda_env.yaml
|--🗎 poetry.lock
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

- `pip-packages.txt`

Contains a list of pip packages and their versions as seen by the pip freeze command. If the project is using conda or poetry using the env files generate for them is prefered.

- `conda_env.yaml`

If Conda is used, this file will be present and will contain the exported Conda env in yaml format.
The enviroment can be recreated using : `conda env create -n ENVNAME --file conda_env.yml`

- `poetry.lock`

The file will be generated if the project is using poetry as package manager.
