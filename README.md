# repo2cli - Notebook repository to a command-line utility backed by the Common Workflow Language (CWL) 

[![Build Status](https://travis-ci.com/terradue-ogc-tb16/repo2cli.svg?branch=develop)](https://travis-ci.com/terradue-ogc-tb16/repo2cli)

`repo2cli` is a command line utility that converts a git repository with a notebook to a CLI utility.

The steps performed are:

- Git clones a repository that contains at least a notebook and a conda environment file
- Creates the environment 
- Publishes the Jupyter kernel associated with that environment
- Cookiecutters a Python project template enabling the creation of the CLI utility that invokes the notebook
- Installs the instantiated Python project 
- Runs the postBuild if included in the repository

## Execution scenario

Notebooks were designed to be executed on a step-by-step execution of cells containing code. 

Instead, this scenario is about the scripted execution of a Notebook. 

The scripted execution of a Notebook requires a mechanism to identify the cells containing the variables to be defined at runtime. 

The Notebook is thus used as a template. During the scripted execution, the template is instantiated, the variable values updated and finally the instantiated notebook cells are executed in a sequential and non-attended process.


`repo2cli` creates the command-line utility to support the scripted execution of a Notebook to:

- Expose the Notebook variables as parameters 
- Instantiates the Notebook (used as a template) updating the variables with the values passed via the CLI
- Execute the cells one after another.
- Save the resulting Notebook 

`repo2cli` follows an nbconvert approach by using its Python API to:

- Parse the Notebook looking for variables to parametrize 
- Replace the variable values at runtime
- Execute the instantiated notebook 
- Save the notebook

The first two steps listed above require the definition of a convention to define parameters in a Notebook. 

We have chosen to use Python dictionaries to define the parameters in a Notebook. 

This choice has the benefit of allowing the defining of additional information to describe the parameters.

CLI utilities provide a help context so providing a description for the parameter seems a good practice.

A parameter could thus be defined as:

```python
ndvi_threshold =  dict([('id', 'ndvi_threshold'),
                        ('description', 'The NDVI threshold, it default value is 0,18'),
                        ('value', '0.18')])
```

The CWL specification has proven its utility to provide a simple way to invoke a command-line utility and to describe a simple workflow as the OGC Application Package.

While the scripted execution of a Notebook doesn’t require using CWL, the execution scenario on an Exploitation Platform does. 

As such, the Python dictionary must include other key/value pairs to allow generating the CWL script that invokes the CLI derived from the Notebook.

The resulting parameter definition thus becomes:

```python
ndvi_threshold =  dict([('id', 'ndvi_threshold'),
                        ('label', 'NDVI threshold'),
                        ('doc', 'The NDVI threshold, its default value is 0.18'),
                        ('value', '0.18'),
                        ('type', 'string')])
```
To define a parameter the provides options, this definition becomes:

```python
false_color_1 = dict([('id', 'false_color_1'),
                      ('label', 'False Color 1 (S5, S3, S2)'),
                      ('doc', 'False Color RGB composite using bands S5, S3 and S2'),
                      ('value', 'Yes'),
                       ('symbols', ['Yes', 'No']),
                       ('type', 'enum')])
```

The creation of a CWL script with a workflow that invokes the CLI requires an additional element defining the CWL workflow metadata: id, doc and label in the CWL terminology. 

Such information is defined with a Python dictionary:

```python
workflow = dict([('label', 'Normalized burn ratio'),
                 ('doc', 'Normalized burn ratio for burned area intensity assessment'),
                 ('id', 'nbr')])
```

## Example

```console
$ repo2cli -r https://github.com/terradue-ogc-tb16/vegetation-index.git 
```

`repo2cli` created:

- a new conda environment named `env_vi`
- a new Jupyter kernel based on the environment above
- a CLI to script the Notebook execution and generate the CWL workflow script

```console
/opt/anaconda/envs/env_vi/bin/vegetation-index --help
usage: vegetation-index [-h] [--kernel KERNEL] [--output NB_TARGET] [--docker DOCKER] [--cwl] [--params] [--input_reference INPUT_REFERENCE] [--aoi AOI]

Vegetation index Vegetation index processor

optional arguments:
  -h, --help            show this help message and exit
  --kernel KERNEL       kernel for notebook execution
  --output NB_TARGET    output notebook
  --docker DOCKER       Sets the docker image for the CWL DockerRequirement
  --cwl                 Prints the CWL script and exits
  --params              Prints the default parameters and exits
  --input_reference INPUT_REFERENCE
                        EO product for vegetation index
  --aoi AOI             Area of interest in WKT
```

The generation of the CWL script is done with:

```console
/opt/anaconda/envs/env_vi/bin/vegetation-index --cwl > vegetation-index.cwl 
```

The generation of the CWL script default parameters is done with:

```console
/opt/anaconda/envs/env_vi/bin/vegetation-index --params > vegetation-index.yml
```

The execution then boils down to:

```console
cwltool vegetation-index.cwl#vegetation-index  vegetation-index.yml
```
## More git repositories with examples

These git repositories contain examples that can be converted to a CLI using `repo2cli`

See the individual READMEs for further details

https://github.com/terradue-ogc-tb16/vegetation-index.git

https://github.com/terradue-ogc-tb16/vegetation-index-ref.git

https://github.com/terradue-ogc-tb16/burned-area.git

https://github.com/terradue-ogc-tb16/burned-area-ref.git

## Installation

### Using conda

```console
conda install -c terradue repo2cli
```

### Development version

Clone this repository.

Create the conda environment with:

```console
conda env create -f environment.yml 
```

Activate the created environment.

Install the `repo2cli` utility with:

```python
python setup.py install 
```

Test the installation:

```console
repo2cli --help
```

This returns:

```
Usage: repo2cli [OPTIONS]

Options:
  -r, --repo-url TEXT  git URL e.g. https://gitlab.com/terradue-
                       ogctb16/eoap/d169-jupyter-nb/eo-processing-hotspot.git

  -b, --branch TEXT    git branch
  --debug              Debug mode
  --help               Show this message and exit.
```
