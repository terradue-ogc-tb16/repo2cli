import os
import sys
import pkg_resources
from cookiecutter.main import cookiecutter
import logging
from .helpers import check_folder
import shutil 

logging.basicConfig(stream=sys.stderr, 
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')

class Lab(object):
    
    def __init__(self, base_image, notebooks, conda_env_spec, post_build_script, repo_url, debug=False):
        
        self.base_image = base_image
        self.notebooks =notebooks
        self.conda_env_spec = conda_env_spec
        self.post_build_script = post_build_script
        self.debug = debug
        self.repo_url = repo_url
        self.cookiecutter_folder = pkg_resources.resource_filename(__package__.split('.')[0],
                                                                  'cookiecutter-nb-blueprint/')
    
    def docker(self):

        if self.debug:
            conda_flag = '--quiet'
        
        '--quiet' if self.debug else ''
        
        dockerfile_content = []

        dockerfile_content.append('FROM {}'.format(self.base_image))

        dockerfile_content.append('MAINTAINER Terradue')

        dockerfile_content.append('USER ${NB_USER}')

        dockerfile_content.append('ADD environment.yml ${HOME}/environment.yml')

        dockerfile_content.append('RUN /opt/anaconda/bin/conda env create --file ${{HOME}}/environment.yml {0} && rm -f ${{HOME}}/environment.yml && /opt/anaconda/bin/conda clean {0} -a -y && /opt/anaconda/envs/{1}/bin/python -m ipykernel install --name {1}'.format('--quiet' if not self.debug else '', self.conda_env_spec['name']))

        dockerfile_content.append('ENV LC_CTYPE=en_GB.utf8 PREFIX=/opt/anaconda/envs/{0}  PATH=/opt/anaconda/envs/{0}/bin/:$PATH'.format(self.conda_env_spec['name']))    

        #dockerfile_content.append('RUN /opt/anaconda/envs/{0}/bin/python -m ipykernel install --name {0}'.format(self.conda_env_spec['name']))

        #dockerfile_content.append('ENV PATH /opt/anaconda/envs/{}/bin/:$PATH'.format(self.conda_env_spec['name']))
        #dockerfile_content.append('RUN chown -R ${{NB_USER}}:${{NB_GID}} /opt/anaconda/envs/{0}'.format(self.conda_env_spec['name']))


        for key, value in self.notebooks.items():

            logging.info('Project template for notebook {}'.format(value))

            data = dict()

            data['project_slug'] = os.path.join('docker', key)
            data['notebook'] = value
            data['repo_url'] = self.repo_url
            data['console_script'] = key
            data['kernel'] = self.conda_env_spec['name']

            check_folder(os.path.join('docker', key))

            app_path = cookiecutter(template=self.cookiecutter_folder, 
                                    extra_context=data, 
                                    no_input=True)

            logging.info('Project template created in: {}'.format(app_path))

            dockerfile_content.append('COPY --chown=jovyan:users {0} ${{HOME}}/{0}\n'.format(key))

            dockerfile_content.append('RUN cd ${{HOME}}/{0} && /opt/anaconda/envs/{1}/bin/python setup.py {2} install'.format(key, self.conda_env_spec['name'], '--quiet' if not self.debug else ''))
            
            if not self.debug:
                dockerfile_content.append('RUN rm -fr ${{HOME}}/{0} && rm -fr ${{HOME}}/__pycache__'.format(self.conda_env_spec['name']))

        dockerfile_content.append('COPY --chown=jovyan:users notebook /workspace/notebook')

        if self.post_build_script is not None:

            logging.info('Found the postBuild file')

            shutil.copyfile(self.post_build_script, os.path.join('docker', os.path.basename(self.post_build_script)))

            dockerfile_content.append('ADD --chown=jovyan:users {0} ${{HOME}}/{0}'.format(os.path.basename(self.post_build_script)))
            dockerfile_content.append('RUN chmod 755 ${{HOME}}/{0} && ${{HOME}}/{0} && rm -f ${{HOME}}/{0}'.format(os.path.basename(self.post_build_script)))
            #dockerfile_content.append('RUN ${{HOME}}/{0} && rm -f ${{HOME}}/{0}'.format(os.path.basename(self.post_build_script)))

        dockerfile_content.append('RUN /opt/anaconda/bin/conda init bash && source ${{HOME}}/.bashrc && conda activate {0} && echo "conda activate {0}" >> ${{HOME}}/.bashrc'.format(self.conda_env_spec['name']))

        dockerfile_content.append('WORKDIR /workspace')

        return dockerfile_content