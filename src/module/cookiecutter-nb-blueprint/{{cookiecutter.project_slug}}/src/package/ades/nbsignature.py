import nbformat as nbf
import logging
import ast
import sys 

logging.basicConfig(stream=sys.stderr, 
                    level=logging.ERROR,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')

def log_param_update(signature, key, param_value):
    
    # log some information but not all of it
    if key in ['base_dir', 'data_path', 'input_catalog', 'input_identifier', 'input_identifier_stack', 'input_reference', 'input_reference_stack']:
      
        msg = 'Update parameter {} with value \'{}\''.format(key, 
                                                             param_value)
        
    elif signature[key]['identifier'] == '_T2Username':
        
        msg = 'Update parameter {} with value \'{}***\''.format(key, 
                                                                param_value[0:3])

    elif signature[key]['identifier'] == '_T2ApiKey':

        msg = 'Update parameter {} with value \'{}***{}\''.format(key, 
                                                                  param_value[0:3],
                                                                  param_value[-3:])
        
    else:
        msg = 'Update parameter {} with value \'{}\''.format(key, 
                                                             param_value)

    logging.info(msg)
    
    return True

def get_signature_notebook(nb_source):
    # builds the notebook signature 
    
    nb = nbf.read(nb_source, 4)

    signature = dict()
    signature['_parameters'] = dict()
    
    for index, cell in enumerate(nb['cells']):
        
        if str(cell['cell_type']) != 'code':
            continue
    
        try:
            root_ast = ast.parse(str(cell['source']))
        except SyntaxError:
            if 'execution_count' in cell.keys():
                logging.warning('Cell #{} (execution #{}) skipped'.format(index, cell['execution_count']))
            else:
                logging.warning('Cell #{} skipped'.format(index))
            continue

        if str(cell['cell_type']) == 'code':

            try:
                names = list({node.id for node in ast.walk(root_ast) if isinstance(node, ast.Name)})

                if len(names) > 2:

                    continue

                if len(names) == 2:

                    if len(set(names) & set(['dict', 'service'])) == 2:

                        # it's the service dictionary
                        exec(str(cell['source'])) in globals(), locals()

                        signature['_service'] = locals()['service']
                        
                    if len(set(names) & set(['dict', 'requirements'])) == 2:

                        # it's the service dictionary
                        exec(str(cell['source'])) in globals(), locals()

                        signature['_requirements'] = locals()['requirements']

                    if len(set(names) & set(['dict', 'service'])) == 1:

                        exec(str(cell['source'])) in globals(), locals()
                        # it's a dict
                        names.remove('dict')

                        if len(set(['identifier', 'value', 'abstract']).intersection(set(locals()[names[0]].keys()))) == 3:

                            signature['_parameters'][names[0]] = locals()[names[0]]
 
            except SyntaxError:
                continue
    
    return signature
    