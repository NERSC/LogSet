#!/usr/bin/env python3

import logging
import sys
logging.debug(str(sys.version_info))
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

# A sample LogSeries:
#:console_logfile
#    a logset:LogSeries ;
#    rdfs:comment ''' a console logfile is timestamped-line-per-entry, generally
#                     named like "console-20170131" and looks like:
#  2017-09-06T15:20:21.827169-07:00 corismw1 craylog: message type: console, connected to port: 5150
#  2017-09-06T15:20:21.827236-07:00 corismw1 craylog: testing connectivity
#                 ''' ;
#    logset:infoType ddict:log_messages ;
#    logset:subjectType ddict:cluster ;
#    logset:logFormatType ddict:timeStampedLogFile ;
#    logset:logFormatInfo "filepattern=console-<date:YYYYMMDD>$" ;
#    logset:logFormatInfo "filepattern=console$" ;
#    logset:logFormatInfo "ts_words=0" ;
#    logset:logFormatInfo "part_word=1" ;
#    .
#


from Node import Node
#import graph
#import graph.Graph.graph as the_graph
from graph import query, localdict_ns
from util import FileInfo, Context, MultiDict
from Subject  import SubjectType
from LogFormatType import LogFormatType
import re
from rdflib.term import Identifier

from typing import Set, List

class InfoType(Node):
    rdf_class = "logset:InfoType"
    getters = {
        'skos:prefLabel': 'ask',
              }
    prompts = {
        'skos:prefLabel':  "A short label for {0}? ",
              }

    label_property:str = 'skos:prefLabel'
    label_alternate:str = 'infotype'

class Pattern(Node):
    rdf_class = "logset:Pattern"
    getters = {
        'logset:tag': 'ask',
        'logset:regex': 'ask'
              }
    required_properties = set(['logset:tag','logset:regex'])
    prompts = {
        'logset:tag': "{0} tag, eg <date:YYYYMMDD> ",
        'logset:regex': "{0} regex, with named groups eg (?P<date>(?P<year>20[0-9]{2}) "
              }
    label_property = 'logset:tag'
    label_alternate = 'new'

    @property
    def uri(self):
        # lazily find uri so there is a chance of deriving a readable one from foaf:name
        if self._uri is None:
            ns = self._namespace or localdict_ns()
            self._uri = self.make_uri(self.label_property, ns)
        return self._uri



# module-level dict mapping each tag to the regex pattern it represents
_tagPatterns = None
def _find_tagPatterns():
    global _tagPatterns
    # query the graph for them
    _tagPatterns = {}
    q = ''' SELECT ?tag ?regex_pattern WHERE {
             ?id a logset:Pattern .
             ?id logset:tag ?tag .
             ?id logset:regex ?regex_pattern .
        } '''
    for row in query(q):
        _tagPatterns[str(row[0])] = str(row[1])

def tagPattern(tag):
    global _tagPatterns
    if _tagPatterns is None:
        _find_tagPatterns()
    return _tagPatterns[tag]

def add_tag_pattern(tag, pattern):
    """ add a new tag and regex to the graph, and to the _tagPatterns dict """
    raise Exception("adding new tag patterns isn't implemented yet!")


def guess_pattern(filename):
    """ work through the list of tag patterns - longest-to-shortest,
        as a proxy for most-unique-first, add yield possible
        filepatterns that the provided filename matches
    """
    for tag in Pattern.known():
        pass


class LogSeries(Node):
    rdf_class = "logset:LogSeries"
    getters = {
        'rdfs:label':           'ask',
        'logset:logFormatType': 'select',
        'logset:infoType':      'select',
        'logset:subjectType':   'select',
        'logset:logFormatInfo': 'skip'   # need to work this out
              }
    required_properties = set(['rdfs:label', 'logset:logFormatType',
                               'logset:infoType','logset:subjectType'])
    prompts = {
        'rdfs:label':           'Give {0} a short identifying lael: ',
        'logset:logFormatType': 'what logformattype is {0}? (TODO get a better question!) ',
        'logset:infoType':      'what type of information does {0} hold? ',
        'logset:subjectType':   'what type of system/component is {0} about? '
              }
    targets = {
        'logset:infoType':      InfoType,
        'logset:subjectType':   SubjectType,
        'logset:logFormatType': LogFormatType
                }

#    finder_query = ''' SELECT ?uri (SAMPLE(?label) as ?label)
#                                   (SAMPLE(?fmttype) as ?fmttype) 
#                                   (SAMPLE(?infotype) as ?infotype) 
#                                   (SAMPLE(?subjtype) as ?subjtype)  WHERE {
#                          ?uri a logset:LogSeries .
#                          ?uri rdfs:label ?label .
#                          ?uri logset:logFormatType ?fmttype .
#                          ?uri logset:infoType ?infotype .
#                          ?uri logset:subjectType ?subjtype .
#                        } GROUP BY ?uri
#                   '''
#    finder_fields = [ 'uri', 'rdfs:label', 'logset:logFormatType',
#                      'logset:infoType', 'logset:subjectType' ]
    label_property:str = 'rdfs:label'
    label_alternate:str = 'log series'

    def __init__(self, properties:MultiDict = None) -> None: 
        super().__init__(properties)
        self._fmtInfo = None
        self._filePatterns = None
        self._logFormatType = None


    @property
    def fmtInfo(self) -> MultiDict:
        if self._fmtInfo is None:
            self._fmtInfo = MultiDict(None)
            for prop in self.get_values('logset:logFormatInfo'):
                key,sep,val = prop.partition('=')
                self._fmtInfo.add(key, val)
        return self._fmtInfo

#                logging.info("prop is {0}".format(prop))
#                logging.info("values is {0}".format())
#                for value in prop:
#                    key,sep,val = prop.partition('=')
#                    logging.info("found key {0} and val {1}".format(key,val))
#                    self._fmtInfo.add(key, val)

    @property
    def filePatterns(self) -> List:
        """ return a list, sorted by pattern length (as a proxy for "most 
            specific to least specific") of filename patterns that generally 
            match this logseries
        """
        if self._filePatterns is None:
            pats = set()
            tags = re.compile('(<[\w:]+>)')
            for pattern in self.fmtInfo['filepattern']:
                # convert from a tag-based-pattern to a regex:
                parts = tags.split(pattern)
                # every 2nd part will be a tag, replace it with corresponding pattern
                tagpatterns = [ tagPattern(t) for t in parts[1::2] ]
                regex_p = ''.join(sum(zip(parts[:-1:2],tagpatterns),())) + parts[-1]
                pats.add(regex_p)
                self._filePatterns = [ re.compile(p) 
                                       for p in sorted(pats, key=len, reverse=True) ]
        return self._filePatterns
        
    @property
    def logFormatType(self):
        if self._logFormatType is None:
            handlerName = self.get_one_value('logset:logFormatType')
            #self._logFormatType = LogFormatType.handlers[handlerName]
        return self._logFormatType

#    logset:logFormatInfo "filepattern=console-<date:YYYYMMDD>$" ;
#    logset:logFormatInfo "filepattern=console$" ;
#    logset:logFormatInfo "ts_words=0" ;
#    logset:logFormatInfo "part_word=1" ;

    @property
    def uri(self):
        # lazily find uri so there is a chance of deriving a readable one 
        if self._uri is None:
            ns = self._namespace or localdict_ns()
            self._uri = self.make_uri(self.label_property, ns)
        return self._uri

    def identify_subjects(self, subject_list):
        """ given a list of high-level subjects, look for specific subject that are
            a partOf one of these and an isSpecific of the subjecttypes relevant to
            this logseries. Returns a list of uris
        """
        as_str = lambda x: "<{0}>".format(str(x)) if isinstance(x,Identifier) else x
        subjtypes = ', '.join([as_str(uri) for uri in self.get_values('logset:subjectType')])
        #logging.debug("my subtypes are: {0}".format(subjtypes))
        subjects = []
        for subj in subject_list:
            # find subjects whose subjecttpye corresponds with subjtype 
            # and that are partOf something in the subjectlist
            q = ''' SELECT ?uri 
                    WHERE {{
                        ?uri a logset:Subject .
                        ?uri logset:isSpecific ?type .
                        ?uri logset:partOf* {0} .
                        FILTER ( ?type in ({1}) ) .
                    }}
                '''.format(as_str(subj), subjtypes)
            subjects += [row[0] for row in self.graph.query(q)]
        #logging.debug("query is: {0}".format(q))
        return subjects

        #for row in graph.Graph.graph.query(q):
        #    logging.info("found matching subject: {0} for {1}".format(row,subj))
            
        # NOTE: the following variations looks more elegant but for a small subject list
        # is slowewr, i guess the multiple parts make an expensive query:
        #subjects = ' '.join([as_str(uri) for uri in subject_list])
        #q = ''' SELECT ?uri ?type
        #        WHERE {{
        #            ?uri a logset:Subject .
        #            ?uri logset:isSpecific ?type .
        #            VALUES ?part {{ {0} }} 
        #            ?uri logset:partOf* ?part .
        #            FILTER ( ?type in ({1}) ) .
        #        }}
        #    '''.format(subjects, subjtypes)


        #for subjtype in self.get_values('logset:subjectType'):
        # actually there can be multiple
        #subjtype_uri = self.get_one_value('logset:subjectType')
        #logging.info("my subjtype uri is: {0}".format(subjtype_uri))
        #my_subjtype = SubjectType.instance(subjtype_uri)
        #logging.info("my subjtype is {0}".format(my_subjtype))
#        preds = 
#        q = ''' SELECT ?subjuri 
#            '''
            
#    def catalog(self, candidates:Set[FileInfo], context:Context) -> Set[FileInfo]:
#        # todo: use subjects passed via context to find relevant specifc subjects
#        # for this logseries
#        matching  = set()
#        remaining = set()
#        context.push(logseries=self)
#        for regex in self.filePatterns():
#            matching += set(filter(lambda x: regex.match(x.filename), candidates))
#        remaining = candidates - matching
#        remaining += self.logFormatType.catalog(matching, context)
#        context.pop(('logseries',))
#        # return something...









