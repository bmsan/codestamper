import subprocess

class GitStamp:
    def __init__(self) -> None:
        pass
   
    def run(args):
        try:
            return subprocess.check_output(args).decode('utf-8')
        except FileNotFoundError as e:
            raise type(e)(e.message + '\n Could not find git executable in system path. You can add it manually using Git(git=/path/to/git)')
    
    @staticmethod
    def hash():
        args = ['git', 'rev-parse', '--short', 'HEAD']
        return subprocess.check_output(args).decode('utf-8')

    @staticmethod
    def create_patch(out_fname):
        args = ['git', 'diff', 'HEAD']
        patch = subprocess.check_output(args).decode('utf-8')
        with open(out_fname, 'wt') as f:
            f.write(patch)

if __name__ == '__main__':
    print(Git.hash())
