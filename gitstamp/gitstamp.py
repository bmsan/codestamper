import subprocess
import os
import platform
from datetime import datetime
try:
    import pwd # Used to get username if os.getlogin fails
except ImportError:
    pass

from typing import List, Union

class GitNotFound(Exception):
    pass

class DirtyWorkspace(Exception):
    pass

def get_username():
    try:
        return os.getlogin()
    except Exception:
        pass
    try:
        return pwd.getpwuid(os.getuid())[0]
    except Exception:
        pass
    return None

def get_hostname():
    try:
        return platform.node()
    except Exception:
        return None

class GitStamp:
    def __init__(self, git_cmd='git') -> None:
        self.git_cmd = git_cmd
   
    def _git(self, args: List[str]):
        try:
            return subprocess.check_output([self.git_cmd] + args).decode('utf-8')
        except FileNotFoundError as e:
            print([x for x in dir(e) if not x.startswith('_')])
            print(e.filename)
            raise GitNotFound(f'Could not find git executable {e.filename} in system path. You can add it manually using GitStamp(git=/path/to/git)')
    
    def _git_config(self, param: str):
        return self._git(['config', '--get', param])

    def git_user_config(self):
        usr = self._git_config('user.name')
        email = self._git_config('user.email')
        return usr, email

    def hash(self):
        return self._git(['rev-parse', '--short', 'HEAD'])
    
    def create_patch(self, out_fname):
        patch = self._git(['diff', 'HEAD'])
        with open(out_fname, 'wt') as f:
            f.write(patch)

    def modified(self):
        return self._git(['ls-files', '-m']).splitlines()
        
    def untracked(self, extensions:List[str]=None):
        if isinstance(extensions, str):
            extensions = [extensions]
        fnames = self._git(['ls-files', '-o', '--exclude-standard']).splitlines()
        if extensions:
            fnames = [el for el in fnames if any(el.endswith(ext) for ext in extensions)]
        return fnames

    def raise_if_dirty(self, modified:bool=True, untracked:Union[bool, List[str]]=True):
        if modified:
            num = self.modified()
            if num:
                raise DirtyWorkspace(f'Encountered {num} modified files')
        if untracked:
            extensions = None if isinstance(untracked, bool) else untracked
            num = self.untracked(extensions)
            if num:
                raise DirtyWorkspace(f'Encountered {num} untracked files')

    def gen_state_info(self, 
            modified_as_patch=True, 
            git_usr=True, 
            node_info=True
        ):
        state = {}
        state['date'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S") 
        state['hash'] = self.hash()
        if git_usr:
            state['git.user'], state['git.email'] = self.git_user_config()
        if node_info:
            state['hostname'] = get_hostname()
            state['username'] = get_username()
        return state

    def gen_mod_patch(self):
        patch = self._git(['diff', 'HEAD'])
    def gen_unpushed_patch():

# 1
# 2
# 3
if __name__ == '__main__':
    print(GitStamp(git_cmd='/usr/bin/git').modified())
    print(GitStamp().untracked())
    print(GitStamp().untracked(extensions=['af']))
    # GitStamp().raise_if_dirty(modified=False, untracked=['bc'])

    print(GitStamp().gen_state_info())
    # GitStamp().raise_if_dirty(modified=True, untracked=True)
    # GitStamp().log_state('log_folder')
    
    # print(untracked, untracked.splitlines())
