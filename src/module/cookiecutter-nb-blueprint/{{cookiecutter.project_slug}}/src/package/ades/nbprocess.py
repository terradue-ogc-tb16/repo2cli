import io
import nbformat as nbf
import ast
import logging
from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError
import sys
import os
from shutil import copy2, copystat, rmtree

logging.basicConfig(stream=sys.stderr, 
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')

class Error(EnvironmentError):
    pass

def copytree(src, dst, symlinks=False, ignore=None):
   
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.isdir(dst):
        os.makedirs(dst)
    
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        copystat(src, dst)
    except OSError as why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.append((src, dst, str(why)))
    if errors:
        raise Error(errors)



def process_notebook(nb_source, signature, nb_target='result.ipynb', kernel='env_app'):
    
    sys.path.append(os.path.dirname(nb_source))
    
    #signature = dict()
    nb = nbf.read(nb_source, 4)

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
            names = list({node.id for node in ast.walk(root_ast) if isinstance(node, ast.Name)})

            if len(names) > 2:

                continue

            if len(names) == 2:

                if 'dict' in names:
                    names.remove('dict')
                else: 
                    continue

                key = names[0]

                if not key in signature['_parameters'].keys():
                    continue

                exec(str(cell['source'])) in globals(), locals()

                key = names[0]
                value = signature['_parameters'][key]['value']

                if len(set(['id', 'value', 'label']).intersection(set(locals()[key].keys()))) >= 3:

                    updated_source = '{} = dict()\n\n'.format(key)

                    for dict_key in signature['_parameters'][key].keys():

                        updated_source = updated_source + '{}[\'{}\'] = \'{}\'\n'.format(key, 
                                                                                         dict_key,
                                                                                         signature['_parameters'][key][dict_key])

                    logging.info('Setting {} to {}'.format(key, updated_source))
                    cell['source'] = updated_source

    ep = ExecutePreprocessor(timeout=50000, kernel_name=kernel)

    out = None

    try:

        out = ep.preprocess(nb, {'metadata': {'path': os.path.dirname(nb_source)}})
                
    except CellExecutionError:
        out = None
        logging.error('Error executing the notebook "{}".'.format(nb_source))

        with io.open(nb_target, 'wt') as file:
            nbf.write(nb, file)

        raise

    finally:
        logging.info('Writing stderr')
        if out is not None:
            for cell in out[0]['cells']:
                if 'outputs' in cell.keys():
                    for output in cell['outputs']:
                        if output['output_type'] == 'stream' and output['name'] == 'stderr':
                            sys.stderr.write(output['text'])
        
        logging.info('Write notebook')  
        with io.open(nb_target, 'wt') as file:
            nbf.write(nb, file)
            