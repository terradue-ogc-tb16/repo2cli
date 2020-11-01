class Workflow():
    
    def __init__(self, signature):
        
        self._wf_class = dict()
        self.signature = signature

        self._wf_class['id'] = self.signature['_workflow']['id']
        self._wf_class['label'] = self.signature['_workflow']['label']
        self._wf_class['doc'] = self.signature['_workflow']['doc']
        self._wf_class['class'] = 'Workflow'
        
        self._wf_class['outputs'] = [{'id': 'wf_outputs',
                                      'outputSource': ['node_1/results'],
                                      'type': {'type': 'array',
                                         'items': 'Directory'}}]
        
        if self.is_scatter():
            
            self.scatter_param = self.get_scatter_input()
        
        else:
            
            self.scatter_param = None
            
        self._wf_class['inputs'] = None

    def get_scatter_input(self):
        
        scatter_input = None
        
        for index, key in enumerate(list(self.signature['_parameters'].keys())):
            
            if 'scatter' in self.signature['_parameters'][key].keys():
            
                scatter_input = 'inp{}'.format(index+1)
        
                break
            
        return scatter_input
        
    def is_scatter(self):
        
        scatter = False
        
        for index, key in enumerate(list(self.signature['_parameters'].keys())):
            
            if 'scatter' in self.signature['_parameters'][key].keys():
            
                scatter = True
        
                break
            
        return scatter

    def set_inputs(self, inputs):
        
        self._wf_class['inputs'] = inputs

    def set_outputs(self, outputs):
        
        self._wf_class['outputs'] = outputs
        
    def set_steps(self, step_inputs):
        
        if self._wf_class['inputs'] is None:
            raise ValueError
        
        if self.is_scatter():
            
            self._wf_class['requirements'] = [{'class': 'ScatterFeatureRequirement'}]

            self._wf_class['steps'] = {'node_1': {'scatter': self.get_scatter_input(),
                                            'scatterMethod': 'dotproduct',
                                            'in': step_inputs,
                                            'out': ['results'],
                                            'run': '#clt'
                                      }
                            }

        
    def to_dict(self):
        
        return self._wf_class