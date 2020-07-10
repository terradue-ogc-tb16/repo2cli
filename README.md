## STAC

Mapping the STAC catalog to the WPS parameters for the EO data inputs

A STACT Collection has an id, title and description

The WPS input gets:

- its identifier from the Collection id
- its title from the Collection title (if None, the from the Collection description)
- its abstract from the Collection description

Python snippet: 

```python
cat = Catalog.from_file(os.path.join(os.path.dirname(nb_source), value))
                        collection = next(cat.get_children())


title = collection.title

# the collection doesn't get the title set during the catalog creation
if title is None:
    title = collection.description

identifier = collection.id
title = title
abstract = collection.description
```

### Open points

#### How to define the cardinality

What is the limit for the inputs?

Options:

- as a property in the properties with the wps namespace ?
- Items.count ? Maybe to harsh and poorly exploitable 


## Can we use more than one collection

This could be the case for two input streams or for a master/slave pair 

input_catalog is one and only one and contains more collections

This yields more WPS input EO parameters

WPS can really tell the stage-in what is an EO reference and what isn't. Who would be staged-in and converted into a STAC

### master/slave

WPS master

WPS slave


### How to define the cardinality

What is the limit for the inputs?

as a property in the properties with the wps namespace ?
