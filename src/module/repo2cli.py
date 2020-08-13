from cookiecutter.main import cookiecutter
import subprocess
import os
import yaml
import click
import sys
import pkg_resources
import logging
import shutil
from urllib.parse import urlparse
from setuptools import find_packages
#from .docker_lab import Lab
#from .docker_prod import Prod

from .helpers import parse_repo_content, update_conda_deps, check_folder


logging.basicConfig(stream=sys.stderr, 
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')


def run_command(command, **kwargs):
    
    process = subprocess.Popen(args=command, stdout=subprocess.PIPE, **kwargs)
    while True:
        output = process.stdout.readline()
        if output.decode() == '' and process.poll() is not None:
            break
        if output:
            logging.info(output.strip().decode())
    rc = process.poll()
    return rc

@click.command()
@click.option('--repo-url', '-r', 'repo_url', help='git URL e.g. https://gitlab.com/terradue-ogctb16/eoap/d169-jupyter-nb/eo-processing-hotspot.git')
@click.option('--branch', '-b', help='git branch', default='master')
@click.option('--debug', is_flag=True, default=False, help='Debug mode')
def main(repo_url, branch, debug):
   
    

    git_bin = 'git'
    docker_bin = 'docker'
    
    check_folder('notebook')
    
    logging.info('Clone {}'.format(repo_url))
    
    if 'GIT_USERNAME' in os.environ:
        
        repo_url = '{}://{}:{}@{}{}'.format(urlparse(repo_url)[0],
                                            os.environ['GIT_USERNAME'], 
                                            os.environ['GIT_TOKEN'],
                                            urlparse(repo_url)[1], 
                                            urlparse(repo_url)[2])
    
    res = run_command([git_bin, 'clone', '--branch', branch, repo_url, 'repo'])

    logging.info('Exit code: {}'.format(res))
    
    if res != 0:
        raise Exception('Git clone step failed')
        sys.exit(res)
    
    # todo check notebooks dict and env.yaml            
    setup, notebooks, conda_env_file, post_build_script = parse_repo_content('repo') 
    
    logging.info('Found the environment.yml file')
    
    if post_build_script is not None:
        logging.info('Found the postBuild file')
        
    # read the environment.yml file 
    with open(conda_env_file) as file:

        conda_env_spec = yaml.load(file, 
                                   Loader=yaml.FullLoader)
    
    logging.info('Updating conda dependencies')
    
    # todo in not prod, don't need lxml and pystac
    if setup is None:
        # notebook 
        
        cookiecutter_folder = pkg_resources.resource_filename(__package__.split('.')[0],
                                                              'cookiecutter-nb-blueprint/')

        
        conda_env_spec['dependencies'] = update_conda_deps(conda_env_spec['dependencies'],
                                                           ['nbformat', 
                                                            'nbconvert', 
                                                            'pyyaml',
                                                            'lxml', 
                                                            'setuptools'])
    
    else:
        # ades file need a few more modules
        conda_env_spec['dependencies'] = update_conda_deps(conda_env_spec['dependencies'],
                                                           ['click', 
                                                            'pyyaml'])

    # create a local folder to put all the files for the docker image build
    check_folder('docker', True)
    
    # copy the environment.yml 
    with open(os.path.join('docker', 'environment.yml'), 'w') as file:
    
        yaml.dump(conda_env_spec, 
                  file, 
                  default_flow_style=False)
    
    # create the conda environment
    # /opt/anaconda/bin/conda env create --file ${{HOME}}/environment.yml
    logging.info('Creating the conda environment')
    
    res = run_command(['/opt/anaconda/bin/conda', 'env', 'create', '--file', os.path.join('docker', 'environment.yml')])
    
    os.environ['PREFIX'] = '/opt/anaconda/envs/{}'.format(conda_env_spec['name'])
    
    logging.info('Exit code: {}'.format(res))
    
    if setup is None:
        # create kernel
        logging.info('Creating the kernel')

        res = run_command('/opt/anaconda/envs/{0}/bin/python -m ipykernel install --name {0}'.format(conda_env_spec['name']).split(' '))

        logging.info('Exit code: {}'.format(res))
                      
                      
    root_wdir = os.getcwd()
    
    
    if setup is None:
        
        for key, value in notebooks.items():

            logging.info('Project template for notebook {}'.format(value))

            data = dict()

            data['project_slug'] = os.path.join('repo', key)
            data['notebook'] = value
            data['repo_url'] = repo_url
            data['branch'] = branch
            data['console_script'] = key
            data['kernel'] = conda_env_spec['name']

            check_folder(os.path.join('docker', key))

            app_path = cookiecutter(template=cookiecutter_folder, 
                                    extra_context=data, 
                                    no_input=True)

            logging.info('Project template created in: {}'.format(app_path))

            os.chdir(os.path.join('repo', key))

            logging.info('Current wdir: {}'.format(os.getcwd()))

            if debug: 
                res = run_command(['/opt/anaconda/envs/{}/bin/python'.format(conda_env_spec['name']),
                                   'setup.py',
                                   'install'])
            else:
                res = run_command(['/opt/anaconda/envs/{}/bin/python'.format(conda_env_spec['name']),
                                   'setup.py',
                                   '--quiet',
                                   'install'])


            os.chdir(root_wdir)

            logging.info('Exit code: {}'.format(res))

        if post_build_script is not None:

            logging.info('Found the postBuild file')
            import stat
            os.chmod(post_build_script, (stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH))

            res = run_command([post_build_script])

            logging.info('Exit code: {}'.format(res))
            #shutil.copyfile(self.post_build_script, os.path.join('docker', os.path.basename(self.post_build_script)))

        if not debug:
            for folder in ['notebook', 'repo']:
                shutil.rmtree(folder)
                
    else:
        
        logging.info('Project template')
        
        pkg = find_packages(os.path.join('repo', 'src'))
        
        logging.info('Project module {}'.format(pkg))
        
        
        
        shutil.copytree(os.path.join(pkg_resources.resource_filename(__package__.split('.')[0],
                                                                     'assets-prj-blueprint'),
                                     'ades'), 
                        os.path.join('repo', 'src', pkg[0], 'ades'))
        
        shutil.copy(os.path.join(pkg_resources.resource_filename(__package__.split('.')[0],
                                                                     'assets-prj-blueprint'),
                                'setup.py'),
                    os.path.join('repo'))
                    
        os.chdir('repo')
        
        if debug: 
            res = run_command(['/opt/anaconda/envs/{}/bin/python'.format(conda_env_spec['name']),
                               'setup.py',
                               'install'])
        else:
            res = run_command(['/opt/anaconda/envs/{}/bin/python'.format(conda_env_spec['name']),
                               'setup.py',
                               '--quiet',
                               'install'])
            
            
        logging.info('Exit code: {}'.format(res))

        os.chdir(root_wdir)
        
        if post_build_script is not None:

            logging.info('Found the postBuild file')
            import stat
            os.chmod(post_build_script, (stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH))

            res = run_command([post_build_script])

            logging.info('Exit code: {}'.format(res))
            
        if not debug:
            for folder in ['repo']:
                shutil.rmtree(folder)
        
if __name__ == "__main__":
    main()