import logging
import sys
import os
import click
from .signature import get_signature
import pkg_resources
import importlib
import yaml

logging.basicConfig(stream=sys.stderr, 
                    level=logging.ERROR,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')

def get_param_type(param_signature):
    
    param_type = None
    
    if 'type' in param_signature:
        
        return param_signature['type']
    
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

    parameters = signature['_parameters']
    
    for key in parameters.keys():

        if 'stac:collection' in parameters[key].keys():

            defaults[key] =  {'class': 'Directory', 'path': os.path.dirname(parameters[key]['stac:href'])}

            if 'scatter' in parameters[key].keys():

                if parameters[key]['scatter'] == 'True':
                    
                    defaults[key] = [ {'class': 'Directory', 'path': os.path.dirname(d)} for d in parameters[key]['stac:href'].split(',')]
                    #defaults[key] = parameters[key]['stac:href'].split(',')


        else:

            if 'min_occurs' in parameters[key].keys():

                defaults[key] = parameters[key]['value']

            if 'max_occurs' in parameters[key].keys():

                if parameters[key]['max_occurs'] == '1':

                    defaults[key] = parameters[key]['value']

                else:

                    defaults[key] = parameters[key]['value'].split(',')

            else:
                defaults[key] = parameters[key]['value']

    return defaults
    


@click.command()
@click.option('--docker', '-d', default=None, help='docker image')
@click.option('--requirement', '-r', type=(str, int), multiple=True, help='set the ResourceRequirement, e.g. ramMin, coresMin')
@click.option('--scatter', is_flag=True, default=False, help='flag to set the ScatterFeatureRequirement on the input_catalog parameter')
@click.option('--params', is_flag=True, default=False, help='flag to print the default parameters as YAML instead of the CWL')
def main(docker, requirement, scatter, params):
        
    
    mod = importlib.import_module(__package__)
    
    # read main() signature
    signature = get_signature(mod)

    
    scatter_on = None
    
    cwl = dict()
    cwl['cwlVersion'] = 'v1.0'
        
    clt_class = dict()

    clt_class['id'] = 'clt'
    
    if docker is not None:
        
        clt_class['hints'] = {'DockerRequirement': {'dockerPull': docker}}
    
    clt_class['class'] = 'CommandLineTool'
    clt_class['baseCommand'] = __package__.split('.')[0].replace('_', '-')
    clt_class['stdout'] = 'std.out'
    clt_class['stderr'] = 'std.err'

    cwl_inputs = dict()
    clt_inputs = dict()
    main_inputs = dict()
    step_inputs = dict()
    cwl_main = dict()

    cwl_main['class'] = 'Workflow'

    
    input_index = 1

    cwl_main['id'] = signature['_workflow']['id']
    cwl_main['label'] = signature['_workflow']['label']
    cwl_main['doc'] = signature['_workflow']['doc']
    
    for index, key in enumerate(list(signature['_parameters'].keys())):
           
        if 'stac:collection' in signature['_parameters'][key].keys():

            if 'scatter' in signature['_parameters'][key].keys():
                if signature['_parameters'][key]['scatter'] == 'True':
                    scatter_on = key
                    scatter_input = 'inp{}'.format(input_index)

                # the Workflow gets the type set in the notebook transformed as an array
                main_inputs[key] = {'type': '{}[]'.format(signature['_parameters'][key]['type']),
                                    'label': signature['_parameters'][key]['label'],
                                    'doc': signature['_parameters'][key]['doc'],
                                    'stac:catalog': 'catalog.json',
                                    'stac:collection': signature['_parameters'][key]['stac:collection']}
                
            else:
                
                # the Workflow gets the type set in the notebook 
                main_inputs[key] = {'type': signature['_parameters'][key]['type'],
                                    'label': signature['_parameters'][key]['label'],
                                    'doc': signature['_parameters'][key]['doc'],
                                    'stac:catalog': 'catalog.json',
                                    'stac:collection': signature['_parameters'][key]['stac:collection']}

            # the CommandLineTool gets the type set in the notebook
            clt_inputs['inp{}'.format(input_index)] = {'type': signature['_parameters'][key]['type'],
                                                        'inputBinding': {'position': input_index,
                                                                         'prefix': '--{}'.format(key)}
                                                       }

        else:

            input_type = get_param_type(signature['_parameters'][key])
            
            

            if input_type == 'enum' and 'symbols' in signature['_parameters'][key].keys():
                
                main_inputs[key] = {'type': {'type': input_type, 
                                             'symbols': signature['_parameters'][key]['symbols']},
                                    'label': signature['_parameters'][key]['label'],
                                    'doc': signature['_parameters'][key]['doc']}

            else:
                
                if 'scatter' in signature['_parameters'][key].keys():
                    
                    if signature['_parameters'][key]['scatter'] == 'True':
                        scatter_on = key
                        scatter_input = 'inp{}'.format(input_index)

                    # the Workflow gets the type set in the notebook transformed as an array
                    main_inputs[key] = {'type': '{}[]'.format(signature['_parameters'][key]['type']),
                                        'label': signature['_parameters'][key]['label'],
                                        'doc': signature['_parameters'][key]['doc']}
                else:
                    
                    main_inputs[key] = {'type': input_type,
                                        'label': signature['_parameters'][key]['label'],
                                        'doc': signature['_parameters'][key]['doc']}

            clt_inputs['inp{}'.format(input_index)] = {'type': input_type,
                                                       'inputBinding': {'position': input_index,
                                                                        'prefix': '--{}'.format(key)}
                                                      }

        step_inputs['inp{}'.format(input_index)] = key

        input_index += 1


    clt_class['inputs'] = clt_inputs

    clt_class['outputs'] = {'results': {'outputBinding': { 'glob': '.'},
                                        'type': 'Any'}} # changed from Directory to Any

    clt_class['stdout'] = 'std.out'
    clt_class['stderr'] = 'std.err'

    if ';' in os.environ['PATH']:

        path = ':'.join([os.path.join(os.environ['PREFIX'], 'bin'), os.environ['PATH'].split(';')[1]])

    else:

        path = ':'.join([os.path.join(os.environ['PREFIX'], 'bin'), os.environ['PATH']])

        
    
    clt_class['requirements'] = {'ResourceRequirement': signature['_requirements'] if '_requirements' in signature.keys() else {},
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


    if params:
        yaml.dump(default_params(signature), sys.stdout, default_flow_style=False)
    else:
        yaml.dump(cwl, sys.stdout, default_flow_style=False)
 
    sys.exit(0)

if __name__ == '__main__':
    
    main()

    


