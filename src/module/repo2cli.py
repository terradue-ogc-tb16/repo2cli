import os
import sys
import click
import pkg_resources
import logging
import shutil
from cookiecutter.main import cookiecutter
from setuptools import find_packages
from .helpers import * #parse_repo_content, update_conda_deps, check_folder


logging.basicConfig(stream=sys.stderr, 
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')


@click.command()
@click.option('--repo-url', '-r', 'repo_url', help='git URL e.g. https://gitlab.com/terradue-ogctb16/eoap/d169-jupyter-nb/eo-processing-hotspot.git', default=None)
@click.option('--branch', '-b', help='git branch', default='master')
@click.option('--debug', is_flag=True, default=False, help='Debug mode')
def main(repo_url, branch, debug):

    
    base_dir = os.getcwd()
    # setup the local folders
    local_path = 'repo'
    
    check_folder('notebook')
    check_folder(local_path)

    # clone the remote repo
    logging.info('Clone {}'.format(repo_url))

    res = get_remote_repo(repo_url, 
                          branch, 
                          local_path)

    logging.info('Exit code: {}'.format(res))

    if res != 0:
        raise Exception('Git clone step failed')
        sys.exit(res)
    
    # parse the repo content    
    # todo check notebooks dict and env.yaml   
    try: 
        notebooks, conda_env_file, post_build_script = parse_repo_content(local_path) 
        
        conda_env_name = get_conda_env_name(conda_env_file)
    except:
        raise
        sys.exit(1)
    
    if post_build_script is not None:
        logging.info('Found the postBuild file')

    
    # create the conda environment
    logging.info('Creating the conda environment')
    
    res = create_conda_env(conda_env_file, 
                           local_path)
    
    logging.info('Exit code: {}'.format(res))
        
    logging.info('Creating the kernel')

    #res = run_command('/opt/anaconda/envs/{0}/bin/python -m ipykernel install --name {0}'.format(conda_env_spec['name']).split(' '))
    
    res = run_command('/opt/anaconda/envs/{0}/bin/python -m ipykernel install --name {0}'.format(conda_env_name).split(' '))

    logging.info('Exit code: {}'.format(res))


    cookiecutter_folder = pkg_resources.resource_filename(__package__.split('.')[0],
                                                          'cookiecutter-nb-blueprint/')

    for key, value in notebooks.items():

        logging.info('Project template for notebook {}'.format(value))

        data = dict()

        data['project_slug'] = os.path.join(local_path, key)
        data['notebook'] = value
        data['repo_url'] = repo_url if repo_url is not None else local_path
        data['branch'] = branch
        data['console_script'] = key
        data['kernel'] = get_conda_env_name(conda_env_file)

        check_folder(os.path.join('docker', key))

        app_path = cookiecutter(template=cookiecutter_folder, 
                                extra_context=data, 
                                no_input=True)

        logging.info('Project template created in: {}'.format(app_path))

        os.chdir(os.path.join('repo', key))

        logging.info('Current wdir: {}'.format(os.getcwd()))

        if debug: 

            options = ['/opt/anaconda/envs/{}/bin/python'.format(conda_env_name),
                               'setup.py',
                               'install']
        else:

            options = ['/opt/anaconda/envs/{}/bin/python'.format(conda_env_name),
                               'setup.py',
                               '--quiet',
                               'install']

        res = run_command(options)

        logging.info('Exit code: {}'.format(res))

    os.chdir(base_dir)
    
    if post_build_script is not None:

        logging.info('Found the postBuild file')
        import stat
        os.chmod(post_build_script, (stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH))

        res = run_command([post_build_script])

        logging.info('Exit code: {}'.format(res))
        #shutil.copyfile(self.post_build_script, os.path.join('docker', os.path.basename(self.post_build_script)))

    if not debug:
        for folder in [local_path]:
            shutil.rmtree(folder)
                
    
if __name__ == "__main__":
    main()