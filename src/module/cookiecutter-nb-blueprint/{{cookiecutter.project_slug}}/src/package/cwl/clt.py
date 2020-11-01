import os

class CommandLineTool():
    
    def __init__(self, signature, executable, docker=None):
        
        self._clt_class = dict()
        self.signature = signature
        self.executable = executable
        self.docker = docker
        
                
        self._clt_class['id'] = 'clt'
    
        if docker is not None:

            self._clt_class['hints'] = {'DockerRequirement': {'dockerPull': self.docker}}

        self._clt_class['class'] = 'CommandLineTool'
        self._clt_class['baseCommand'] = self.executable
        self._clt_class['stdout'] = 'std.out'
        self._clt_class['stderr'] = 'std.err'

        self._clt_class['outputs'] = {'results': {'outputBinding': { 'glob': '.'},
                                            'type': 'Directory'}} 

        self._clt_class['stdout'] = 'std.out'
        self._clt_class['stderr'] = 'std.err'

        env_vars = {'PATH' : self.get_path()}

        if 'PREFIX' in os.environ:

            env_vars['PREFIX'] = os.environ['PREFIX']



        self._clt_class['requirements'] = {'ResourceRequirement': self.signature['_requirements'] if '_requirements' in self.signature.keys() else {},
                                     'EnvVarRequirement' : {'envDef':
                                                            env_vars}}

    def set_inputs(self, inputs):
        
        self._clt_class['inputs'] = inputs

    def set_outputs(self, outputs):
        
        self._clt_class['outputs'] = outputs
        
    def to_dict(self):
        
        return self._clt_class

    def get_path(self):
    
        path = os.environ['PATH']

        if ';' in path:

            path = os.environ['PATH'].split(';')[1]

        if 'PREFIX' in os.environ:

            path = ':'.join([os.path.join(os.environ['PREFIX'], 'bin'), path])

        return path