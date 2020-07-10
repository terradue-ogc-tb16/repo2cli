from setuptools import setup, find_packages
from io import open
import os

console_scripts = """
[console_scripts]
{{cookiecutter.console_script}}={0}.ades.cli:main
{{cookiecutter.console_script}}-cwl={0}.ades.cwl:main""".format(find_packages('src')[0])

def package_files(where):
    paths = []
    
    for directory in where:
        
        for (path, directories, filenames) in os.walk(directory):
            for filename in filenames:
                
                if ('.json' in filename) or ('.py' in filename) or ('.ipynb' in filename):
                    paths.append(os.path.join(path, filename).replace('src/package/', ''))
    
    return paths



extra_files = package_files(['src/package/notebook'])

setup(entry_points=console_scripts,
      packages=find_packages(where='src'),
      package_dir={'': 'src'},
      package_data = {'': extra_files})