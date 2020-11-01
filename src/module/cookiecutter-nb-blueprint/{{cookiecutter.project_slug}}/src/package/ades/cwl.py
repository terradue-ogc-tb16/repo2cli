from .clt import CommandLineTool
from .wf import Workflow
from .aninput import AnInput

def cwl(signature, executable, docker=None):

    clt_inputs = dict()
    wf_inputs = dict()
    step_inputs = dict()

    for index, key in enumerate(list(signature['_parameters'].keys())):

        an_input = AnInput(signature, key, index)

        clt_inputs['inp{}'.format(index+1)] = an_input.get_clt_input()
        wf_inputs[key] = an_input.get_wf_input()
        step_inputs['inp{}'.format(index+1)] = key
        
    wf = Workflow(signature)

    wf.set_inputs(wf_inputs)
    wf.set_steps(step_inputs)
    
    clt = CommandLineTool(signature, 
                          executable, 
                          docker=None)
    
    clt.set_inputs(clt_inputs)
    
    cwl = dict()

    cwl['cwlVersion'] = 'v1.0'

    cwl['$graph'] = [clt.to_dict(), wf.to_dict()]
    
    return cwl

def default_params(signature, scatter_on=None):
    
    # TODO check the scatter
    wf = Workflow(signature)

    is_scatter = wf.is_scatter()
    
    scatter_input = wf.get_scatter_input()
    
    defaults = dict()

    parameters = signature['_parameters']
    
    for key in parameters.keys():


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