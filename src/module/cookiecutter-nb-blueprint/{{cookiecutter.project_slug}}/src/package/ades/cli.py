from __future__ import absolute_import
import os 
import sys
from argparse import ArgumentParser, HelpFormatter
import ast 
import io
import pkg_resources
import glob
from shutil import ignore_patterns, rmtree
import yaml

from .nbprocess import process_notebook, copytree
from .nbsignature import get_signature_notebook
from .cwl import default_params, cwl

try:
    # for Python 2.7
    reload(sys)
    sys.setdefaultencoding('utf8')

except NameError:  
    pass

import logging

logging.basicConfig(stream=sys.stderr, 
                    level=logging.ERROR,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')

signature = None
     
def log_param_update(signature, key, param_value):
    
    # log some information but not all of it
    if signature['_parameters'][key]['id'] == '_T2Username':
        
        msg = 'Update parameter {} with value \'{}***\''.format(key, 
                                                                param_value[0:3])

    elif signature['_parameters'][key]['id'] == '_T2ApiKey':

        msg = 'Update parameter {} with value \'{}***{}\''.format(key, 
                                                                  param_value[0:3],
                                                                  param_value[-3:])
        
    else:
        msg = 'Update parameter {} with value \'{}\''.format(key, 
                                                             param_value)

    logging.info(msg)
    
    return True
    
class Formatter(HelpFormatter):

    # use defined argument order to display usage
    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = 'usage: '

        # if usage is specified, use that
        if usage is not None:
            usage = usage % dict(prog=self._prog)

        # if no optionals or positionals are available, usage is just prog
        elif usage is None and not actions:
            usage = '%(prog)s' % dict(prog=self._prog)
        elif usage is None:
            prog = '%(prog)s' % dict(prog=self._prog)
            # build full usage string
            action_usage = self._format_actions_usage(actions, groups) # NEW
            usage = ' '.join([s for s in [prog, action_usage] if s])
            # omit the long line wrapping code
        # prefix with 'usage:'
        return '%s%s\n\n' % (prefix, usage)
    
def main():

    kernel = '{{cookiecutter.kernel}}'
    # use package resources to access the notebook 
    # and any.py file in the egg notebook folder
    notebook_path = pkg_resources.resource_filename(__package__.split('.')[0], '{{cookiecutter.notebook}}')
    notebook_folder = pkg_resources.resource_filename(__package__.split('.')[0], 'notebook/')
    
    
    # to clean
    to_clean = ['.{}'.format(f.replace(notebook_folder, '')) for f in glob.glob(os.path.join(notebook_folder, '*/'), recursive=True)]

    # get the notebook signature
    signature = get_signature_notebook(notebook_path)

    # create the CLI 
    parser = ArgumentParser(formatter_class=Formatter, 
                            description='{}\n{}'.format(signature['_workflow']['label'], 
                                                        signature['_workflow']['doc']))

    
    # add kernel as parameter
    parser.add_argument('--kernel',
                        action='store',
                        dest='kernel',
                        default=kernel,
                        help='kernel for notebook execution')
    
    parser.add_argument('--output',
                        action='store',
                        dest='nb_target',
                        default='result.ipynb',
                        help='output notebook')
    
    parser.add_argument('--docker',
                        action='store',
                        dest='docker',
                        default=None,
                        help='Sets the docker image for the CWL DockerRequirement')
    
    parser.add_argument('--cwl',
                        action='store_true',
                        dest='print_cwl',
                        default=False,
                        help='Prints the CWL script and exits')
    
    parser.add_argument('--params',
                        action='store_true',
                        dest='print_defaults',
                        default=False,
                        help='Prints the default parameters and exits')
    
    if not '_parameters' in signature.keys():
        raise ValueError()
    
    parameters = signature['_parameters']
    
    for key in parameters.keys():
        
        if parameters[key]['type'] == 'enum' and 'symbols' in parameters[key].keys():
            
            parser.add_argument('--{}'.format(key),
                                action='store',
                                dest=key,
                                default=parameters[key]['value'],
                                help=parameters[key]['doc'],
                                choices=parameters[key]['symbols'])
        else:

            parser.add_argument('--{}'.format(key),
                                action='store',
                                dest=key,
                                default=parameters[key]['value'],
                                help=parameters[key]['doc'])

    # parse the CLI
    args = parser.parse_args()
    
    if args.print_cwl:
        
        yaml.dump(cwl(signature, 
                      os.path.basename(notebook_path).replace('.ipynb', ''),
                      docker=args.docker), 
                  sys.stdout, 
                  default_flow_style=False)
        sys.exit(0)
    
    if args.print_defaults:
        
        yaml.dump(default_params(signature),
                  sys.stdout,
                  default_flow_style=False)
        sys.exit(0)
    
    # update notebook signature with values set from CLI
    for key, value in vars(args).items():

        if key in ['nb_target', 'kernel', 'docker', 'print_cwl', 'print_defaults']:
            continue

        log_param_update(signature, key, value)
        
        if 'stac:collection' in parameters[key].keys():
            
            # value is a folder
            parameters[key]['stac:href'] = os.path.join(value, 'catalog.json') 
            
        else:
        
            parameters[key]['value'] = value 
        
    signature['_parameters'] = parameters
    
    # process the notebook
    logging.info('Process notebook with: {}'.format(args.kernel))   

    process_notebook(notebook_path, 
                     signature, 
                     args.nb_target, 
                     args.kernel)
    
    # copy the results produced except 
    # the run.ipynb and any *.py file used
    copytree(notebook_folder, 
             '.',
             ignore=ignore_patterns('*.py', 
                                    '__pycache__',
                                    os.path.basename('{{cookiecutter.notebook}}')))
    
    logging.info('Clean-up')
    for p in ['.ipython', '.cache']:
        
        if os.path.exists(p) and os.path.isdir(p):

            rmtree(p)
    
    for p in to_clean:

        if os.path.exists(p) and os.path.isdir(p):

            rmtree(p)
        
    
    logging.info('Done!')

    sys.exit(0)

if __name__ == '__main__':

    main()
