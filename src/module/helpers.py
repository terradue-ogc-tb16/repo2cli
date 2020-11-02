import os
import os
import shutil
import fnmatch
import subprocess
from urllib.parse import urlparse
import yaml

def run_command(command, **kwargs):
    
    process = subprocess.Popen(args=command, stdout=subprocess.PIPE, **kwargs)
    while True:
        output = process.stdout.readline()
        if output.decode() == '' and process.poll() is not None:
            break
        if output:
            print(output.strip().decode())
    rc = process.poll()
    return rc

def get_remote_repo(repo_url, branch, target):
    
    git_bin = 'git'

    if 'GIT_USERNAME' in os.environ:

        repo_url = '{}://{}:{}@{}{}'.format(urlparse(repo_url)[0],
                                            os.environ['GIT_USERNAME'], 
                                            os.environ['GIT_TOKEN'],
                                            urlparse(repo_url)[1], 
                                            urlparse(repo_url)[2])

    res = run_command([git_bin, 
                       'clone', 
                       '--branch', 
                       branch, 
                       repo_url, 
                       target])

    return res

def get_conda_env_name(conda_env_file):
    
    # read the environment.yml file 
    with open(conda_env_file) as file:

        conda_env_spec = yaml.load(file, 
                                   Loader=yaml.FullLoader)

    return conda_env_spec['name']
        
def create_conda_env(conda_env_file, target):
    
    # read the environment.yml file 
    with open(conda_env_file) as file:

        conda_env_spec = yaml.load(file, 
                                   Loader=yaml.FullLoader)
    
    conda_env_spec['dependencies'] = update_conda_deps(conda_env_spec['dependencies'])
    
    # copy the environment.yml 
    with open(os.path.join(target, 'environment.yml'), 'w') as file:
    
        yaml.dump(conda_env_spec, 
                  file, 
                  default_flow_style=False)
    
    
    res = run_command(['/opt/anaconda/bin/conda', 
                       'env', 
                       'create', 
                       '--file', 
                       os.path.join(target, 
                                    'environment.yml')])
    
    os.environ['PREFIX'] = '/opt/anaconda/envs/{}'.format(conda_env_spec['name'])
    
    return res


def parse_repo_content(folder):
    
    post_build_script = None
    conda_env_file = None
    
    notebooks = dict()

    for root, dirs, files in os.walk(folder):
        for name in files:

            if fnmatch.fnmatch(name, '*.ipynb'):
                notebook_path = os.path.join(root, name)


                notebooks[os.path.basename(notebook_path).replace('.ipynb', '')] = notebook_path

            if fnmatch.fnmatch(name, 'environment.yml'):

                conda_env_file = os.path.join(root, name)
                
            if fnmatch.fnmatch(name, 'postBuild'):
                
                post_build_script = os.path.join(root, name)
            
       
    if conda_env_file is None:
        
        raise Exception('environment.yml file not found')
        
    return notebooks, conda_env_file, post_build_script


def update_conda_deps(current):
        
    current.extend(['nbformat', 
                    'nbconvert', 
                    'pyyaml',
                    'lxml', 
                    'setuptools'])
        
    return current


def check_folder(folder, create=False):
    
    if os.path.exists(folder) and os.path.isdir(folder):
    
        shutil.rmtree(folder)
    
    if create:
        os.mkdir(folder)
        
