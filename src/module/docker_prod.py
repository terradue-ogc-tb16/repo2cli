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
class Prod(object):
    
    def __init__(self, base_image, notebooks, conda_env_spec, post_build_script, repo_url, tag, debug=False):
        
        self.base_image = base_image
        self.notebooks =notebooks
        self.conda_env_spec = conda_env_spec
        self.post_build_script = post_build_script
        self.repo_url = repo_url
        self.debug = debug
        self.tag = tag
        self.cookiecutter_folder = pkg_resources.resource_filename(__package__.split('.')[0],
                                                              'cookiecutter-nb-production-centre/')  
    
    def docker(self):

        dockerfile_content = []

        dockerfile_content.append('FROM {}'.format(self.base_image))

        dockerfile_content.append('MAINTAINER Terradue')

        dockerfile_content.append('USER root')

       # dockerfile_content.append('ENV LC_CTYPE en_GB.utf8')

        dockerfile_content.append('ADD environment.yml ${HOME}/environment.yml')

        dockerfile_content.append('RUN yum install -y yum-plugin-ovl && yum install -y wget which unzip mlocate && wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/anaconda && mkdir -p /application/job')
            
        dockerfile_content.append('ENV HOME=/home/nobody PATH=/opt/anaconda/bin:$PATH LC_CTYPE=en_GB.utf8 PREFIX=/opt/anaconda/envs/{0} PATH=/opt/anaconda/envs/{0}/bin/:$PATH'.format(self.conda_env_spec['name']))    
   
        dockerfile_content.append('ADD environment.yml ${HOME}/environment.yml')
        
        dockerfile_content.append('RUN /opt/anaconda/bin/conda env create --file ${{HOME}}/environment.yml {0} && rm -f ${{HOME}}/environment.yml && /opt/anaconda/bin/conda clean {0} -a -y && /opt/anaconda/envs/{1}/bin/python -m ipykernel install --name {1}'.format('--quiet' if not self.debug else '', self.conda_env_spec['name']))
        
        #dockerfile_content.append('RUN /opt/anaconda/envs/{0}/bin/python -m ipykernel install --name {0}'.format(self.conda_env_spec['name']))
        
        #dockerfile_content.append('ENV PATH /opt/anaconda/envs/{}/bin/:$PATH'.format(self.conda_env_spec['name']))
        
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

            dockerfile_content.append('COPY --chown=nobody:nobody {0} ${{HOME}}/{0}\n'.format(key))

            dockerfile_content.append('RUN cd ${{HOME}}/{0} && /opt/anaconda/envs/{1}/bin/python setup.py install'.format(key, self.conda_env_spec['name']))
       
            if not self.debug:
                dockerfile_content.append('RUN rm -fr ${{HOME}}/{0} && rm -fr ${{HOME}}/__pycache__'.format(key))
    
            dockerfile_content.append('RUN /opt/anaconda/envs/{}/bin/{}-app --stdout > /application/application.xml'.format(self.conda_env_spec['name'], 
                                                                                                                            os.path.basename(app_path)))
            # it doesn't work yet with STAC
            #dockerfile_content.append('RUN /opt/anaconda/envs/{}/bin/{}-cwl -d "{}" --scatter > /application/job/_workflow.cwl'.format(self.conda_env_spec['name'], 
            #                                                                                                                           os.path.basename(app_path),
            #                                                                                                                           self.tag))
                                                                                                                                       
            #dockerfile_content.append('RUN /opt/anaconda/envs/{}/bin/{}-cwl -d "{}" --scatter --params > /application/job/_params.yaml'.format(self.conda_env_spec['name'],  
            #                                                                                                                                 os.path.basename(app_path),
            #                                                                                                                                 self.tag))
            
            dockerfile_content.append('RUN echo "#!/bin/bash" > /application/job/run.sh && echo "source /opt/anaconda/etc/profile.d/conda.sh" >> /application/job/run.sh && echo "conda activate $(basename $PREFIX)" >> /application/job/run.sh && echo "export GPT_BIN=$PREFIX/snap/bin/gpt" >> /application/job/run.sh  &&   echo "${PREFIX}/bin/run-node-1  -k $( basename $PREFIX )" >> application/job/run.sh &&  chmod 755 /application/job/run.sh && chown  nobody:nobody /application/job/run.sh')
            
            
            #dockerfile_content.append('RUN chown -R nobody:nobody /application && chmod 755 /application/job/run.py')
        dockerfile_content.append('RUN chown -R nobody:nobody /opt/anaconda/envs/{0} && chown -R nobody:nobody ${{HOME}} '.format(self.conda_env_spec['name']))        
   
        
        #dockerfile_content.append('ENV PREFIX /opt/anaconda/envs/{}'.format(conda_env_spec['name']))


        # run here the postBuild 
        # https://repo2docker.readthedocs.io/en/latest/config_files.html#postbuild-run-code-after-installing-the-environment
        if self.post_build_script is not None:

            logging.info('Found the postBuild file')

            shutil.copyfile(self.post_build_script, os.path.join('docker', os.path.basename(self.post_build_script)))

            dockerfile_content.append('ADD --chown=nobody:nobody {0} ${{HOME}}/{0}'.format(os.path.basename(self.post_build_script)))
            dockerfile_content.append('RUN chmod 755 ${{HOME}}/{0}'.format(os.path.basename(self.post_build_script)))
            dockerfile_content.append('USER nobody')
            dockerfile_content.append('RUN ${{HOME}}/{0} && rm -f ${{HOME}}/{0}'.format(os.path.basename(self.post_build_script)))
        
        dockerfile_content.append('RUN /opt/anaconda/bin/conda init bash && source ${{HOME}}/.bashrc && conda activate {0} && echo "conda activate {0}" >> ${{HOME}}/.bashrc'.format(self.conda_env_spec['name']))
            
        dockerfile_content.append('WORKDIR ${HOME}')
        
        return dockerfile_content