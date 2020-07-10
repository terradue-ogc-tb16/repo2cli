import subprocess

def main():
    
    repo_url = '{{cookiecutter.repo_url}}'
    branch = '{{cookiecutter.branch}}'
    repo_type = 'git'
    
    clone_to_dir = 'src/package'
        
    subprocess.check_output(
                [repo_type, 'clone', '--branch', branch, repo_url, 'notebook'],
                cwd=clone_to_dir,
                stderr=subprocess.STDOUT)
 
if __name__ == '__main__':
    
    main()