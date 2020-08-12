from setuptools import setup, find_packages
from io import open
import os

console_scripts = """
[console_scripts]
repo2cli=module.repo2cli:main
"""

def package_files(where):
    paths = []
    
    for directory in where:
        
        for (path, directories, filenames) in os.walk(directory):
            for filename in filenames:
                paths.append(os.path.join(path, filename).replace('src/module/', ''))
    
    return paths

extra_files = package_files(['src/module/cookiecutter-nb-blueprint', 
                             'src/module/assets-prj-blueprint'])


setup(entry_points=console_scripts,
      packages=find_packages(where='src', exclude=['cookiecutter-nb-*', 'assets-prj-*']),
      package_dir={'': 'src'},
      package_data = {'': extra_files})

