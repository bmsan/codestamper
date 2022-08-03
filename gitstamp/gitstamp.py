import subprocess
import os
import platform
from datetime import datetime
import json
import sys

try:
    import pwd # Used to get username if os.getlogin fails
except ImportError:
    pass

from typing import List, Union

class GitNotFound(Exception):
    pass

class DirtyWorkspace(Exception):
    pass

class LastPushedCommitNA(Exception):
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

def pip_packages():
    out = {}
    reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode('utf-8')
    for line in reqs.splitlines():
        key, val = line.split('==')
        out[key] = val
    return out

class GitStamp:
    def __init__(self, git_cmd='git') -> None:
        self.git_cmd = git_cmd
   
    def _git(self, args: List[str], to_file:str=None):
        cmd = [self.git_cmd] + args
        try:
            if to_file:
                with open(to_file, 'w') as fout:
                    subprocess.run(cmd, stdout=fout)
            else:
                return subprocess.check_output(cmd).decode('utf-8')
        except FileNotFoundError as e:
            if e.filename == to_file:
                raise 
            else:
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

    def get_state_info(self, 
            git_usr=True, 
            node_info=True,
            python_info=True
        ):
        state = {}
        state['date'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S") 
        git = state['git'] = {}
        git['hash'] = self.hash()
        if git_usr:
            git['user'], git['email'] = self.git_user_config()
        if node_info:
            node = state['node'] = {}
            node['username'] = get_username()
            uname = platform.uname()
            for key in ['node', 'system', 'version', 'release']:
                try:
                    val = getattr(uname, key)
                except Exception:
                    val = None
                node[key] = val
        if python_info:
            py = state['python'] = {}
            py['version'] = sys.version
            
            py['pip_packages'] = pip_packages()
        return state

    def gen_mod_patch(self, folder, fname='mod.patch'):
        os.makedirs(folder, exist_ok=True)
        if fname is None:
            fname = f'mod.patch'
        self._git(['diff', 'HEAD'],to_file=os.path.join(folder, fname))


    def get_unpushed_start_end(self):
        push_marker = 'refs/remotes/'
        lines = self._git(['reflog', '--all']).splitlines()
        if push_marker in lines[0]:
            return None, None
        end = lines[0].split(' ', 1)[0]
        start = None
        for line in lines[1:]:
            if push_marker in line:
                start = line.split(' ', 1)[0]
                break
        if start is None:
            raise LastPushedCommitNA('Could not identify last pushed commit.')
        return start, end

           
    def gen_unpushed_patch(self, folder, fname=None):
        os.makedirs(folder, exist_ok=True)
        start, end = self.get_unpushed_start_end()
        if fname is None:
            fname = f'unpushed{start}-{end}.patch'
        if start:
            self._git(['diff', start, end], to_file=os.path.join(folder, fname))

    def log_state(self, folder, 
            modified_as_patch=True, 
            unpushed_as_patch=False,
            git_usr=True,
            node_info=True,
            python_info=True
        ):
        os.makedirs(folder, exist_ok=True)
        info = self.get_state_info(git_usr, node_info, python_info)
        with open(os.path.join(folder, 'code_state.json'), 'wt') as f:
            json.dump(info, f, indent=2)
        self.gen_mod_patch(folder)
        self.gen_unpushed_patch(folder)
# 1
# 2
# 3
# 4
if __name__ == '__main__':
    GitStamp().log_state('git_log')
    x = GitStamp().gen_unpushed_patch('gogu.patch')
    print(x)
    exit()
    print(GitStamp(git_cmd='/usr/bin/git').modified())
    print(GitStamp().untracked())
    print(GitStamp().untracked(extensions=['af']))
    # GitStamp().raise_if_dirty(modified=False, untracked=['bc'])

    print(GitStamp().get_state_info())
    # GitStamp().raise_if_dirty(modified=True, untracked=True)
    # GitStamp().log_state('log_folder')
    
    # print(untracked, untracked.splitlines())
