#!/usr/bin/env python3

import sys
sys.path.append('/global/homes/s/sleak/.local/cori/3.6-anaconda-4.4/lib/python3.6/site-packages')
import rdflib

import TimeStampedLogFile.py

# a console log file looks like:
# TimeStampedLogFile('console-20170906', rootpath=target_path)
# while a message lorgf file is:
# TimeStampedLogFile('messages-20170906',rootpath=target_path, tsword=1) 
# TODO write a factory (or at least a method) to create these


class LogSet:
    """ a collection of files described by an index.ttl """

    def read(self):
        """ read the index.ttl file """
        pass

    def write(self):
        """ (over)write the index.ttl file """
        pass



if __name__ == '__main__':

    # simple first attempt: given a path, walk it for files whose name matches 
    # the pattern of a known LogSeries, and create an index.ttl describing what
    # was found 
    import sys
    path = sys.argv[1]

    # get the data dictionary:
    dict_path = 'https://raw.githubusercontent.com/NERSC/LogSet/master/etc/dict#'
    dgraph = rdflib.ConjunctiveGraph().parse(dict_path[:-1]+'.ttl', format='turtle')

    # and use it to find the vocab:
    namespaces = dict([n for n in gindex.namespaces()])
    vocab_path = namespaces['logset']
    vgraph = rdflib.ConjunctiveGraph().parse(vocab_path[:-1]+'.ttl', format='turtle')


    
