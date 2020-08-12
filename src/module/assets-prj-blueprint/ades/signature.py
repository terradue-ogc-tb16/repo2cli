import inspect

def get_signature(module):
    
    # read the child app Python module main function signature
    signature = dict()

    for index, arg in enumerate(inspect.getargspec(module.main).args):

        signature[arg] = [item[1] for item in inspect.getmembers(module) if arg in item][0]
    
    signature['service'] = module.service

    return signature