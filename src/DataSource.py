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
        'dct:description': "A brief description of {0}? " 
              }
    label_property = 'rdfs:label'
    label_alternate = 'datasource'


class Files(DataSource):
    rdf_node = 'ddict:files'

    def catalog(self, topdir:Set[FileInfo], context:Context) -> Set[FileInfo]:
        baselen = len(topdir)+1
        remaining = set([ FileInfo(topdir, path[baselen:], f)
                          for path, d, files in os.walk(topdir) for f in files ])

        # keep track of the known relevant logseries to compare samples 
        # of new filepatterns against
        #known_logseries = set()

        # for a Files datasource, only file-based log formats make sense:
        for fmttype in FileBasedLogFormatType.known({'logset:dataSource': self.uri}):
            logging.info("found logformattype {0}".format(fmttype.uri))
            context.push(logFormatType=str(fmttype.uri))
            #fmttype_uri = graph.Graph.geturi(fmttype.uri)
            for logseries in LogSeries.known({'logset:logFormatType':fmttype.uri}):
                logging.info("found logseries {0} {1}".format(fmttype.uri,str(logseries)))
                #known_logseries.add(logseries)
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
            
            break # code below is incomplete, jump out for now
            # things to check:
            #   - is the mediatype suitable for a fmttype?
            #        (need to call on the fmttype for that I think, because
            #        eg FilePerTimePoint has inode mediatype, but the sample will
            #        be a file, so we'd be looking for the directory rather
            #        that the file itself
            #      - does the filename have something in common with a 
            #        known logseries (of this fmttype)
            #        (for each known pattern, split the filename by that pattern
            #        and compare each non-matching part with the filepatterns 
            #        of this logseries

            # "clues" - parts of filename not matching patterns
            # (what if 2 parts of the filename match a pattern?)
            # if we get a clue called, eg "-" then it is probably not a
            # useful one .. so skip too-short clues (maybe that don't have
            # [a-z]+ in them
            # ah, then from known logseries, split tags out and look for [a-z]+
            # then propose a logseries if it has a matching [a-z]+ word
            clues = set()
            
            too_short = 2 # only consider words longer than this
            re_word = re.compile('[a-zA-Z_]+')
            for p in Pattern.known():
                tag = p.properties.one('logset:tag')
                regex = re.compile(p.properties.one('logset:regex'))
                parts = regex.split(sample.filename)
                # parts has the non-matching parts of the filename
                if len(parts)==1:
                    continue # no match
                for part in parts:
                    #find just the words
                    # this will automagically handle <label:> patterns too
                    for w in re_word.findall(part):
                        if len(w)>too_short:
                            clues.add(w)
            
            re_tag = re.compile('(<[\w:]+>)')
            # TODO might be worth caching:
            for fmttype in FileBasedLogFormatType.known({'logset:dataSource': self.uri}):
                if not fmttype.right_mime_type(sample):
                    continue
                for logseries in LogSeries.known({'logset:logFormatType':fmttype.uri}):
                    # TODO I think this belongs as a method of LogSeries:
                    # eg if logseries.describes(sample): logseries.add_filepattern ; break
                    for p in logseries.fmtInfo['filepattern']:
                        parts = re_tag.split(p)
                        for w in re_word.findall(part):
                            if w in clues:
                                # this might be a new filepattern for this logseries,
                                # show the user a sample and ask them to verify
                                # TODO: make logset:sampleContents a property of LogSeries
                                # and show it to the user
                                logging.info("{0} might be a {1}".format(str(sample),str(logseries)) )
                # TODO break out of inner loops if the candidate is found
                else: 
                    pass
                    # ask the user if this file looks like this logformattype (eg
                    # "is this a timestampedlogfile?"
                    # might be a function of the handler, to ask user if this is right
                    # thing, and verify that it can read the fields it requires, eg the 
                    # timestamp and component word
            # having found or created a logsereis, now find other candidates that match
            # it and catalog them


        return remaining


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

