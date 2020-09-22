import subprocess
import os
import shutil

def main():
    
    
    
    repo_url = '{{cookiecutter.repo_url}}'
    
    if os.path.isdir(repo_url):
        
        shutil.copytree(repo_url, 'src/package')
    
    else:
        
        branch = '{{cookiecutter.branch}}'
        repo_type = 'git'

        clone_to_dir = 'src/package'

        subprocess.check_output(
                    [repo_type, 'clone', '--branch', branch, repo_url, 'notebook'],
                    cwd=clone_to_dir,
                    stderr=subprocess.STDOUT)

if __name__ == '__main__':
    
    main()