import yaml
import logging
import click
import pkg_resources
import sys
from .nbsignature import get_signature_notebook
import os

logging.basicConfig(stream=sys.stderr, 
                    level=logging.ERROR,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')

def get_param_type(param_signature):
    
    param_type = None
    
    if not all(elem in list(param_signature) for elem in ['min_occurs', 'max_occurs']):
        
        # if not set, add the key and its default value
        
        if not 'min_occurs' in param_signature.keys():

            param_signature['min_occurs'] = 1

        if not 'max_occurs' in param_signature.keys():

            param_signature['max_occurs'] = 2

    # cast to int
    param_signature['min_occurs'] = int(param_signature['min_occurs']) 
    param_signature['max_occurs'] = int(param_signature['max_occurs'])
    
    if (param_signature['min_occurs'] == 0) & (param_signature['max_occurs'] == 1):

        param_type = 'string?'

    if (param_signature['min_occurs'] == 0) & (param_signature['max_occurs'] > 1):

        param_type = 'string[]?'

    if (param_signature['min_occurs'] == 1) & (param_signature['max_occurs'] == 1):

        param_type = 'string'

    if (param_signature['min_occurs'] == 1) & (param_signature['max_occurs'] > 1):

        param_type = 'string[]'

    if (param_signature['min_occurs'] > 1) & (param_signature['max_occurs'] > 1):

        param_type = 'string[]'
    
    return param_type

def default_params(signature, scatter_on=None):
    
    defaults = dict()

    for key in signature.keys():
         
        if key in ['service']:

            continue

        if key in ['input_reference']:
             
            if 'stac:collection' in signature[key].keys():
                if not scatter_on is None:
                    defaults[key] =  [{'class': 'Directory', 'path': os.path.dirname(signature[key]['stac:href'])}]
                else:
                    defaults[key] =  {'class': 'Directory', 'path': os.path.dirname(signature[key]['stac:href'])}

            else:
                defaults[key] = signature[key]['value'].split(',')
                
        elif key in ['input_reference_stack']:
             
            if 'stac:collection' in signature[key].keys():
                
                defaults[key] =  {'class': 'Directory', 'path': os.path.dirname(signature[key]['stac:href'])}

            else:
                
                defaults[key] = signature[key]['value'].split(',')
        
        else:
            if 'stac:collection' in signature[key].keys():

                defaults[key] =  {'class': 'Directory', 'path': os.path.dirname(signature[key]['stac:href'])}

            else:
                
                if 'min_occurs' in signature[key].keys():
                    
                    defaults[key] = signature[key]['value']
                    
                if 'max_occurs' in signature[key].keys():

                    if signature[key]['max_occurs'] == '1':
                        
                        defaults[key] = signature[key]['value']
                        
                    else:
                        
                        defaults[key] = signature[key]['value'].split(',')
                        
                else:
                    defaults[key] = signature[key]['value']
                
    return defaults
    
    
def cwl(signature, executable, docker=None, scatter_on=None, requirement=''):
    
    cwl = dict()
    cwl['cwlVersion'] = 'v1.0'
        
    clt_class = dict()

    clt_class['id'] = 'clt'
    
    if docker is not None:
        
        clt_class['hints'] = {'DockerRequirement': {'dockerPull': docker}}
    
    clt_class['class'] = 'CommandLineTool'
    clt_class['baseCommand'] = executable
    clt_class['stdout'] = 'std.out'
    clt_class['stderr'] = 'std.err'

    cwl_inputs = dict()
    clt_inputs = dict()
    main_inputs = dict()
    step_inputs = dict()
    cwl_main = dict()

    cwl_main['class'] = 'Workflow'

    
    input_index = 1

    for index, key in enumerate(list(signature.keys())):
       
        if key in ['service']:
            
            cwl_main['id'] = signature[key]['identifier']
            cwl_main['label'] = signature[key]['title']
            cwl_main['doc'] = signature[key]['abstract']
            
            continue

        elif key == 'input_reference':

            if 'stac:collection' in signature[key].keys():
                
                if scatter_on == key:
                    param_type = 'Directory[]'
                else:
                    param_type = 'Directory'
                    
                main_inputs[key] = {'type': param_type,
                                    'label': signature[key]['title'],
                                    'doc': signature[key]['abstract'],
                                    'stac:collection': signature[key]['stac:collection']}
                
                clt_inputs['inp{}'.format(input_index)] = {'type': 'Directory',
                                                           'inputBinding': {'position': input_index,
                                                                            'prefix': '--{}'.format(key)}
                                                       }
                
            else:

                if 'data_path' in signature.keys():
                    
                    main_inputs[key] = {'type': 'string[]',
                                        'label': signature[key]['title'],
                                        'doc': signature[key]['abstract']}
                                
                
                else:
                    
                    main_inputs[key] = {'type': 'Directory[]',
                                        'label': signature[key]['title'],
                                        'doc': signature[key]['abstract']}
                                

                clt_inputs['inp{}'.format(input_index)] = {'type': 'string',
                                                           'inputBinding': {'position': input_index,
                                                                            'prefix': '--{}'.format(key)}
                                                          }

            step_inputs['inp{}'.format(input_index)] = key

            if scatter_on == key:
                scatter_input = 'inp{}'.format(input_index)

        elif key == 'data_path':

            main_inputs[key] = 'string'

            clt_inputs['inp{}'.format(input_index)] = {'type': 'string',
                                                       'default': '/workspace/data',
                                                       'inputBinding': {'position': input_index,
                                                                        'prefix': '--{}'.format(key)}
                                                      }

            step_inputs['inp{}'.format(input_index)] = key
       
        else:
            
            if 'stac:collection' in signature[key].keys():
                
                if scatter_on == key:
                    param_type = 'Directory[]'
                else:
                    param_type = 'Directory'
                
                
                main_inputs[key] = {'type': param_type,
                                    'label': signature[key]['title'],
                                    'doc': signature[key]['abstract'],
                                    'stac:collection': signature[key]['stac:collection']}
                
                
                clt_inputs['inp{}'.format(input_index)] = {'type': 'Directory',
                                                            'inputBinding': {'position': input_index,
                                                                             'prefix': '--{}'.format(key)}
                                                           }
                
            else:
                
                input_type = get_param_type(signature[key])

                main_inputs[key] = {'type': input_type,
                                    'label': signature[key]['title'],
                                    'doc': signature[key]['abstract']}

                clt_inputs['inp{}'.format(input_index)] = {'type': 'string',
                                                           'inputBinding': {'position': input_index,
                                                                            'prefix': '--{}'.format(key)}
                                                          }

            step_inputs['inp{}'.format(input_index)] = key

        input_index += 1


    clt_class['inputs'] = clt_inputs

    clt_class['outputs'] = {'results' : {'outputBinding': { 'glob': '.'},
                                             'type': 'Any'                                       
                                 }} # changed from Directory to Any

    clt_class['stdout'] = 'std.out'
    clt_class['stderr'] = 'std.err'

    if ';' in os.environ['PATH']:

        path = ':'.join([os.path.join(os.environ['PREFIX'], 'bin'), os.environ['PATH'].split(';')[1]])

    else:

        path = ':'.join([os.path.join(os.environ['PREFIX'], 'bin'), os.environ['PATH']])

    clt_class['requirements'] = {'ResourceRequirement': dict(requirement),
                                     'EnvVarRequirement' : {'envDef':
                                                            {'PATH' : path, 
                                                             'PREFIX': os.environ['PREFIX']}}}
                                    

    


    cwl_main['inputs'] = main_inputs

    if not scatter_on is None:
        
        cwl_main['requirements'] = [{'class': 'ScatterFeatureRequirement'}]
        
        cwl_main['steps'] = {'node_1': {'scatter': scatter_input,
                                        'scatterMethod': 'dotproduct',
                                        'in': step_inputs,
                                        'out': ['results'],
                                        'run': '#clt'
                                  }
                        }
        
        cwl_main['outputs'] = [{'id': 'wf_outputs',
                                'outputSource': ['node_1/results'],
                                        'type': {'type': 'array',
                                                    'items': 'Directory'}}
                              ]


    else:
        
        cwl_main['steps'] = {'node_1': {'in': step_inputs,
                                       'out': ['results'],
                                       'run': '#clt'
                                  }
                        } 

        cwl_main['outputs'] = [{'id': 'wf_outputs',
                                'outputSource': ['node_1/results'],
                                'type': {'type': 'array',
                                         'items': 'Directory'}}]

    cwl['$namespaces'] = {'stac': 'http://www.me.net/stac/cwl/extension'}
    
    cwl['$graph'] = [clt_class, cwl_main]


    return cwl
    


@click.command()
@click.option('--docker', '-d', default=None, help='docker image')
@click.option('--requirement', '-r', type=(str, int), multiple=True, help='set the ResourceRequirement, e.g. ramMin, coresMin')
@click.option('--scatter', default=None, help='Set the ScatterFeatureRequirement on the provided parameter')
@click.option('--params', is_flag=True, default=False, help='flag to print the default parameters as YAML instead of the CWL')
def main(docker, requirement, scatter, params):

    notebook_path = pkg_resources.resource_filename(__package__.split('.')[0], '{{cookiecutter.notebook}}')
    notebook_folder = pkg_resources.resource_filename(__package__.split('.')[0], 'notebook/')
    
    signature = get_signature_notebook(notebook_path)

    if params:
        yaml.dump(default_params(signature,
                                scatter_on=scatter),
                  sys.stdout,
                  default_flow_style=False)
    else:
       
        yaml.dump(cwl(signature, 
                      os.path.basename(notebook_path).replace('.ipynb', ''),
                      docker=docker,
                      scatter_on=scatter, 
                     requirement=requirement), 
                  sys.stdout, 
                  default_flow_style=False)
 
    sys.exit(0)

if __name__ == '__main__':
    
    main()
