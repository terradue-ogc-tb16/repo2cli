from __future__ import absolute_import
import os, fnmatch
import sys
from argparse import ArgumentParser, HelpFormatter
from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError
import nbformat as nbf
import ast 
import io
import pkg_resources
from .nbprocess import process_notebook, copytree
from .nbsignature import get_signature_notebook, log_param_update
import glob

from shutil import ignore_patterns, rmtree

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

    logging.info('initial content: {}'.format(to_clean))
    
    
    # get the notebook signature
    signature = get_signature_notebook(notebook_path)
    
    # create the CLI 
    parser = ArgumentParser(formatter_class=Formatter, 
                            description='{}\n{}'.format(signature['service']['title'], 
                                                        signature['service']['abstract']))

    
    parser.add_argument('--output',
                                action='store',
                                dest='nb_target',
                                default='result.ipynb',
                                help='output notebook')
    

    for key in signature.keys():

        if key in ['service']: continue

        if key in ['input_catalog']:
            
            parser.add_argument('--{}'.format(key),
                                action='store',
                                dest=key,
                                default=signature[key]['value'],
                                help='Path to the STAC input catalog')
            continue
            
        if key in ['data_path', 'base_dir']:
            
            parser.add_argument('--{}'.format(key),
                                action='store',
                                dest=key,
                                default=signature[key]['value'],
                                help='Folder containing the data')
     
        else:

            if 'allowed_values' in signature[key].keys():
                parser.add_argument('--{}'.format(key),
                                    action='store',
                                    dest=key,
                                    default=signature[key]['value'],
                                    help=signature[key]['abstract'],
                                    choices=signature[key]['allowed_values'].split(','))
            else:

                parser.add_argument('--{}'.format(key),
                                    action='store',
                                    dest=key,
                                    default=signature[key]['value'],
                                    help=signature[key]['abstract'])

    # parse the CLI
    args = parser.parse_args()

    logging.info('Using kernel {}'.format(kernel))

    # update the data_path key (if available)
    if 'data_path' in vars(args).keys():
        log_param_update(signature, 'data_path', vars(args)['data_path'])        
        signature['data_path']['value'] = vars(args)['data_path']
    
    # update notebook signature with values set from CLI
    for key, value in vars(args).items():
     
        if key in ['nb_target', 'kernel', 'stage_in', 'data_path']:
            continue

        log_param_update(signature, key, value)
        
        if 'stac:collection' in signature[key].keys():
            
            # value is a folder
            signature[key]['stac:href'] = os.path.join(value, 'catalog.json') 
        
        else:
        
            signature[key]['value'] = value 
        
  
    
    # process the notebook
    logging.info('Process notebook')   

    process_notebook(notebook_path, 
                     signature, 
                     args.nb_target, 
                     kernel)
    
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
