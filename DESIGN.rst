######
LogSet
######

************************
Requirements Envisioning
************************

Usage Model
===========

The initial/essential use cases are:

Create a bare-minimum logset from a bunch of logfiles or other source
  :ID: _`UC1`
  :Preconditions: 
    - we can read a valid ontology and dictionary
    - we have at least one logfile to describe
  :Postconditions:
    An `index.ttl` file is created in a target location describing each of the 
    LogSeries that will be part of the logset, the files comprising it, any 
    annotation databases, etc
  :Notes: 
    - if an index.ttl already exists at the target location, the tool should
      warn/guide the user about replacing or updating it
    - "or other source": eg a curl command or sql query
    - we also need a "grows over time" data dictionary describing how to 
      handle a particular type of file

Report on a described dataset
  :ID: _`UC2`
  :Preconditions: 
    - we can read a valid ontology
    - we have either an `index.ttl` (ie unpacked logset) or a packed logset
      (some sort of tar, tgz, etc file containing an `index.ttl`)
  :Postconditions:
    A summary of the dataset is produced, showing:
      - the provenance of the logset (system, when it was collected, 
        who by/who to contact, etc)
      - the timespan it covers
      - the logseries it incorporates
      - the annotation sets it includes
  :Notes: 
    Additional optional reports might include:
      - whether the logset data corresponds with the decriptions in `index.ttl`
      - statistics about eg the number of events described in the annotations

Pack a logset
  :ID: _`UC3`
  :Notes: 
    Packing requires gathering the described data to one location, updating the
    paths in the `index.ttl` file, etc, so needs special support, but unpacking
    is as simple as untarring a file, so should not need special support

Add annotations to a logset
  :ID: _`UC4`

Extract a timeslice from a logset
  :ID: _`UC5`

A further use case would be, given a catalog of LogSets, find relevant things 
eg for a particular time period, or for a particular failure mode as described 
in annotations

  
Initial Domain Model
====================

The domain is the various log and annotations files that make up a dataset, and
the description/definition files that allow humans and tools to make sense of 
them

.. code-block:: plantuml

@startuml
object logset {
   an aggregate of logs, annotations, 
   an index, spanning a timeframe
}
object logseries {
   a specific log, possibly split 
   into several files (eg console, 
   with a file per day)
}
object logfile {
   a single file within a logset, 
  belonging to a 
}
logset 1 --> "*" logseries
logseries "1" -- "*" logfile

object vocab {
   the ontology describing classes of
   things that comprise a logset
}
object dictionary {
   collection of logseries descriptions
   (eg what a console log looks like, etc),
   separate to vocab as changes more 
   often, but also separate to logset and
   used in multiple logsets
}
vocab -- dictionary : < instantiates
logseries -- dictionary : < describes


@enduml

.. end


UI Model
========

Git-like command line interface, with a command for each essential use case, eg
``logset create ....``. The options available for each command should be 
sufficient to completely perform it, but a "guided interactive" mode should 
also be available. (For example, when adding to a logset, the tool should 
present what it thinks are the files of a single logseries, ask the user to 
confirm, find the time range if it can and ask user to confirm, etc).


************************
Architecture Envisioning
************************

A component/OO architecture seems to fit the requirements and domain best: 

.. code-block:: plantuml

@startuml
object command {
  controller for each essential use case
}
object CreateCommand {
  example: finds logfiles, reads and updates dictionary 
  to guess what series, timestamp format, etc, calls 
  appropriate log reader class to get range of log, 
  populates an index.ttl file with descriptions of the 
  data. Can interact with user to get info
}
object InfoCommand {
  example: reads an index.ttl from either a dir or tar,
  produces a report about the logset (and eg whether it 
  knows how to read each part)
}
object dictionary {
  structure corresponding to dict.ttl, with eg the 
  regex/arg needed to find the timestamp of a log entry
}
object vocab {
  used to validate dict.ttl and index.ttl, also has 
  registry of which class to instantiate to handle 
  each logfile/logseries
}
object index {
  structure corresponding to index.ttl
}
object logfile
object package

command --> vocab : < ontology_graph

@enduml
.. end


**************
Feature Design
**************

* Create a logset (`UC1`_)

  Basic flow will be like:
  - setup base graph (vocab + dict)
  - for each file in filesystem (or tar) walk starting at provided path:
    - attempt to add the file to the graph: (this might be its own use case)
      - does filename correspond to a pattern in dict? (known series)
        - yes: work out what is in this file, check if graph already contains 
          this data, do something sensible if so, else add the subgraph
        - no: either skip it or ask user what they want to do

* Read, verify and report on a logset (`UC2`_)




