class AnInput():

    def __init__(self, signature, key, index):
        
        self._input = dict()
        
        self._signature = signature
        self._key = key
        self._index = index
        
        self.input_signature = self._signature['_parameters'][self._key]
        
        self.input_type = self.get_param_type()
        
    def get_param_type(self):
    
        param_type = None

        if 'type' in self.input_signature:

            return self.input_signature['type']

        if not all(elem in list(self.input_signature) for elem in ['min_occurs', 'max_occurs']):

            # if not set, add the key and its default value

            if not 'min_occurs' in self.input_signature.keys():

                self.input_signature['min_occurs'] = 1

            if not 'max_occurs' in self.input_signature.keys():

                self.input_signature['max_occurs'] = 2

        # cast to int
        self.input_signature['min_occurs'] = int(self.input_signature['min_occurs']) 
        self.input_signature['max_occurs'] = int(self.input_signature['max_occurs'])

        if (self.input_signature['min_occurs'] == 0) & (self.input_signature['max_occurs'] == 1):

            param_type = 'string?'

        if (self.input_signature['min_occurs'] == 0) & (self.input_signature['max_occurs'] > 1):

            param_type = 'string[]?'

        if (self.input_signature['min_occurs'] == 1) & (self.input_signature['max_occurs'] == 1):

            param_type = 'string'

        if (self.input_signature['min_occurs'] == 1) & (self.input_signature['max_occurs'] > 1):

            param_type = 'string[]'

        if (self.input_signature['min_occurs'] > 1) & (self.input_signature['max_occurs'] > 1):

            param_type = 'string[]'

        return param_type 
    
    def parse_input(self):
        
        wf_input = None
        clt_input = None
        
        if self.input_type == 'enum' and 'symbols' in self.input_signature.keys():
                
            wf_input = {'type': {'type': self.input_type, 
                                         'symbols': self._signature['_parameters'][self._key]['symbols']},
                                'label': self._signature['_parameters'][self._key]['label'],
                                'doc': self._signature['_parameters'][self._key]['doc']}
            
        else: 
        
            if 'scatter' in self._signature['_parameters'][self._key].keys():

                if self._signature['_parameters'][self._key]['scatter'] == 'True':
                    scatter_on = self._key
                    scatter_input = 'inp{}'.format(self._index+1)

                    # the Workflow gets the type set in the notebook transformed as an array
                    wf_input = {'type': '{}[]'.format(self._signature['_parameters'][self._key]['type']),
                                        'label': self._signature['_parameters'][self._key]['label'],
                                        'doc': self._signature['_parameters'][self._key]['doc']
                               }
            else:

                wf_input = {'type': self.input_type,
                                    'label': self._signature['_parameters'][self._key]['label'],
                                    'doc': self._signature['_parameters'][self._key]['doc']
                           }
    
        clt_input = {'type': self.input_type,
                     'inputBinding': {'position': int(self._index+1),
                                      'prefix': '--{}'.format(self._key)}
                    }
    
     
        return wf_input, clt_input
    
    def get_wf_input(self):
        
        return self.parse_input()[0]
    
    def get_clt_input(self):
        
        return self.parse_input()[1]