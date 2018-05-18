#!/usr/bin/env python3

import logging
import sys
logging.debug(str(sys.version_info))
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

from Node import Node
from util import FileInfo, Context, MultiDict
from typing import Set
from FileBasedLogFormatType import FileBasedLogFormatType
from LogSeries import LogSeries
import os
from graph import get_shorthand

classes = {} 
def factory(node: str):
    cls = classes[node]
    properties = MultiDict(uri=[cls.rdf_node])
    return cls(properties=properties)

class DataSource(Node):
    rdf_class = 'logset:DataSource'
    getters = {
        'rdfs:label':      'ask',
        'dct:description': 'ask'
              }
    prompts = {
        'rdfs:label':      "A short label for {0}? ",
        'dct:description': "A breif description of {0}? " 
              }
    label_property = 'rdfs:label'
    label_alternate = 'datasource'


class Files(DataSource):
    rdf_node = 'ddict:files'

    def catalog(self, topdir:Set[FileInfo], context:Context) -> Set[FileInfo]:
        baselen = len(topdir)+1
        remaining = set([ FileInfo(topdir, path[baselen:], f)
                          for path, d, files in os.walk(topdir) for f in files ])

        # for a Files datasource, only file-based log formats make sense:
        for fmttype in FileBasedLogFormatType.known({'logset:dataSource': self.uri}):
            logging.info("found logformattype {0}".format(fmttype.uri))
            context.push(logFormatType=str(fmttype.uri))
            #fmttype_uri = graph.Graph.geturi(fmttype.uri)
            for logseries in LogSeries.known({'logset:logFormatType':fmttype.uri}):
                logging.info("found logseries {0} {1}".format(fmttype.uri,str(logseries)))
                # get logseries to narrow the subjects a bit
                # then push the narrowed subject list to context
                subjects = logseries.identify_subjects(context['subjects'])
                context.push(filepatterns=logseries.filePatterns,
                             formatinfo=logseries.fmtInfo,
                             subjects=subjects, logseries_uri=logseries.uri)
                remaining = fmttype.catalog(remaining, context)
                context.pop(('filepatterns','formatinfo','subjects'))
            context.pop(('logFormatType',))

        while len(remaining)>0:
            # try describing new logseries for them:
            logging.warning("{0:d} files remain to be catalogued!".format(len(remaining)))
            sample = remaining.pop()
            

        return remaining


#        for regex in self.filePatterns():
#            matching += set(filter(lambda x: regex.match(x.filename), candidates))
#                context.push(
#
#
#
#            todo = set(LogSeries.known({'logset:LogFormatType':fmttype.uri}))
#            done = set()
#            logging.debug("todo has: {0}".format([', '.join(str(i)) for i in todo])))
#
#            while len(todo) > 0:
#            logseries = todo.pop()
#            remaining = logseries.catalog(remaining, context)
#            done.add(pattern)
#            todo.remove(pattern)
#            if len(todo)==0:
#                # we need to come up with more logseries
#                break # for now
        
        # we call on the logseries for suitable subjects and filepatterns
        # then we call on logformattype to work out how to collate files
        #   into concretelogs
        # logformattype yields concretelogs

        # if we run out of logseries and still have more files, need to ask
        # user to describe a logseries for remaining files
        # the logseries sets the logformattype (partly via mediatype, partly
        # by asking the user), with the constraint that it must be a 

        # for each suitable logformattype
        #     find logseries using that logformattype

classes[Files.rdf_node] = Files

