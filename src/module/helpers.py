import os
import shutil
import fnmatch

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
                
    return notebooks, conda_env_file, post_build_script


def update_conda_deps(current, extend):
    
    for dep in extend:

        if not dep in current:
            
            current.append(dep)
    
    return current


def check_folder(folder, create=False):
    
    if os.path.exists(folder) and os.path.isdir(folder):
    
        shutil.rmtree(folder)
    
    if create:
        os.mkdir(folder)
        
