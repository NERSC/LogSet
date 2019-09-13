######
LogSet
######

Tools for manipulating a set of system logs described with RDF/Turtle

A goal for the Resilience Project is to produce a dataset of system logs and
related information, along with outage logs and a set of annotations, that
external researchers can use to develop/improve analytics tools by running
tools over our provided data (eg attempting to identify events, and predict
them before they occur).

A secondary goal is a recipe for collecting this data (what to collect, where
from, how, and how to clean/pre-process it)

Meanwhile a goal of the CUG SMWG is to define a reference architecture for
collecting, storing and analysing Cray system logs, while an internal goal for
NERSC is to enable discoverability and interoperability between various data-
collection and monitoring related projects that would otherwise be siloed.

All of these goals can be addressed by defining a machine-and-human readable
vocabulary for describing log-type data, and providing some tools to create and
use this metadata. **This** repository aims to provide such a vocabulary and a
set of tools for describing and managing  data via that vocabulary.

`Turtle/RDF`_ offers rich semantics for describing concepts and data in terms
of other known concepts and data, more so than for example yaml. It is machine-
readable and also easily human readable, so we will use it to define a
vocabulary, a data dictionary and the contents of a LogSet

.. _`Turtle/RDF`: https://www.w3.org/TR/turtle/


To prepare:
 - install anaconda 3.6+
 - make an environment for anno:
    conda create --name=anno python=3.6
 - use it:
    conda activate anno
 - add logset to it:
    cd $logset_repo
    python ./setup.py install
 - cd back to anno
    test with `python -c "import logset"`



 - conda env create -f environment.yml
 - conda activate logsets
 - pip install -e requirements-conda.txt
