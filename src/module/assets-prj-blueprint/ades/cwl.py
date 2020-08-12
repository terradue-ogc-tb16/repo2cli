import yaml
import logging
import click
import pkg_resources
import sys
from .signature import get_signature
import os
from pystac import Catalog, Collection
import importlib

logging.basicConfig(stream=sys.stderr, 
                    level=logging.ERROR,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')

@click.command()
@click.option('--docker', '-d', default='no image provided', help='docker image')
@click.option('--requirement', '-r', type=(str, int), multiple=True, help='set the ResourceRequirement, e.g. ramMin, coresMin')
@click.option('--scatter', is_flag=True, default=False, help='flag to set the ScatterFeatureRequirement on the input_catalog parameter')
@click.option('--params', is_flag=True, default=False, help='flag to print the default parameters as YAML instead of the CWL')
def main(docker, requirement, scatter, params):

    mod = importlib.import_module(__package__)
    
    # read main() signature
    signature = get_signature(mod)

    first_step = 'first'
    
    cwl = dict()
    cwl_inputs = dict()

    cwl['cwlVersion'] = 'v1.0'


    node_workflow = dict()

    node_workflow['id'] = 'node'  
    node_workflow['hints'] = {'DockerRequirement': {'dockerPull': docker}}
    
    node_workflow['class'] = 'CommandLineTool'
    node_workflow['baseCommand'] = __package__.split('.')[0].replace('_', '-')
    node_workflow['stdout'] = 'std.out'
    node_workflow['stderr'] = 'std.err'

    defaults = dict()

    for key in signature.keys():
         
        if key in ['service', 'input_identifier']:

            continue

        if key in ['input_reference']:
 
            defaults[key] = signature[key]['value'].split(',')
        
        elif key in ['base_dir', 'data_path']:
          
            defaults[key] = {'class': 'Directory', 
                             'location': signature[key]['value'], 
                             'path': signature[key]['value']}
        
        elif key in ['input_catalog']:

            if scatter:
                defaults[key] =  [{'class': 'File', 'path': p } for p in signature[key]['value'].split(',')]
            else:
                defaults[key] =  {'class': 'File', 'path': signature[key]['value']}
                
        else:
            
            defaults[key] = signature[key]['value']

    # read the parameters 
    node_inputs = dict()
    main_inputs = dict()
    step_inputs = dict()

    input_index = 1

    for index, key in enumerate(list(signature.keys())):

        if key in ['service', 'input_identifier']:

            continue

            
        if key in ['base_dir', 'data_path']:
   
            main_inputs[key] = 'Directory'
            
            node_inputs['arg{}'.format(input_index)] = {'type': 'Directory',
                                                        'inputBinding': {'position': input_index,
                                                                         'prefix': '--{}'.format(key), 
                                                                         'valueFrom': '$(self.path)'}
                                                       }
            
            
            step_inputs['arg{}'.format(input_index)] = key

        elif key == 'input_reference':

            main_inputs[key] = {'type': 'string[]', 
                                'label': signature[key]['title'],
                                'ows:abstract': signature[key]['abstract']}
            

            node_inputs['arg{}'.format(input_index)] = {'type': 'string',
                                                        'inputBinding': {'position': input_index,
                                                                         'prefix': '--{}'.format(key)}
                                                       }

            step_inputs['arg{}'.format(input_index)] = key

            scatter_input = 'arg{}'.format(input_index)
        
        elif key == 'input_catalog':
            
            input_catalog = os.path.join(notebook_folder,
                                         signature[key]['value'])
            
            cat = Catalog.from_file(input_catalog)
            
            collections = dict()

            for col in iter(cat.get_children()):

                collections[col.id] = {'wps:identifier':col.id,
                                       'wps:title': col.title,
                                       'wps:abstract': col.description}
            
            if scatter: 
                
                scatter_input = 'arg{}'.format(input_index)
                
                main_inputs[key] = {'type': 'File[]', 
                                    'label': signature[key]['title'],
                                    'ows:abstract': signature[key]['abstract']}
                
                node_inputs['arg{}'.format(input_index)] = {'type': 'File',
                      'inputBinding': {'position': input_index,
                                       'prefix': '--{}'.format(key)},
                      'stac:catalog': { 'stac:collection': collections }
                     }
                
            else:
                main_inputs[key] = {'type': 'File', 
                                    'label': signature[key]['title'],
                                    'ows:abstract': signature[key]['abstract']}
                
                node_inputs['arg{}'.format(input_index)] = {'type': 'File',
                      'inputBinding': {'position': input_index,
                                       'prefix': '--{}'.format(key)},
                      'stac:catalog': { 'stac:collection': collections }
                     } 
                
            step_inputs['arg{}'.format(input_index)] = key
            
        else:
            
            main_inputs[key] = {'type': 'string', 
                                'label': signature[key]['title'],
                                'ows:abstract': signature[key]['abstract']}
                                
                                

            node_inputs['arg{}'.format(input_index)] = {'type': 'string',
                      'inputBinding': {'position': input_index,
                                       'prefix': '--{}'.format(key)}
                                                       }
        
            step_inputs['arg{}'.format(input_index)] = key

        input_index += 1


    node_workflow['inputs'] = node_inputs

    node_workflow['outputs'] = {'results' : {'outputBinding': { 'glob': '.'},
                                             'type': 'Any'                                       
                                 }} # changed from Directory to Any

    node_workflow['stdout'] = 'std.out'
    node_workflow['stderr'] = 'std.err'

    if ';' in os.environ['PATH']:

        path = os.environ['PATH'].split(';')[1]

    else:

        path = os.environ['PATH']

    node_workflow['requirements'] = {'ResourceRequirement': dict(requirement),
                                     'EnvVarRequirement' : {'envDef':
                                                            {'PATH' : path, 
                                                             'PREFIX': os.environ['PREFIX']}}}
                                    

    cwl_main = dict()

    cwl_main['class'] = 'Workflow'

    cwl_main['id'] =  signature['service']['identifier']
    cwl_main['label'] = signature['service']['title']
    cwl_main['doc'] = signature['service']['abstract']
    
    cwl_main['inputs'] = main_inputs

    if scatter:
        cwl_main['requirements'] = [{'class': 'ScatterFeatureRequirement'}]
        
        cwl_main['steps'] = {first_step: {'scatter': scatter_input,
                                   'scatterMethod': 'dotproduct',
                                  'in': step_inputs,
                                   'out': ['results'],
                                   'run': '#node'
                                  }
                        }    

    else:
        
        cwl_main['steps'] = {first_step: {'in': step_inputs,
                                       'out': ['results'],
                                       'run': '#node'
                                  }
                        } 


    if scatter:

        cwl_main['outputs'] = [{'id': 'wf_outputs',
                                'outputSource': ['{}/results'.format(first_step)],
                                        'type': {'type': 'array',
                                                    'items': 'Directory'}}
                              ]


    else:

        cwl_main['outputs'] = [{'id': 'wf_outputs',
                                'outputSource': ['{}/results'.format(first_step)],
                            'type': {'type': 'array',
                                     'items': 'Directory'}}]

    cwl['$namespaces'] = {'ows': 'http://www.opengis.net/ows/1.1',
                          'stac': 'http://www.me.net/stac/cwl/extension'}

        
        
    
    cwl['$graph'] = [node_workflow, cwl_main]

    if params:
        yaml.dump(defaults, sys.stdout, default_flow_style=False)
    else:
        yaml.dump(cwl, sys.stdout, default_flow_style=False)
 
    sys.exit(0)

if __name__ == '__main__':
    
    main()
