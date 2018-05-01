#!/usr/bin/env python3

import logging
import sys
logging.debug(sys.version_info)
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

# example of a LogSeries:
#:messages_logfile
#    a logset:LogSeries ;
#    logset:infoType dict:log_messages ;
#    logset:logFormatType dict:timeStampedLogFile ;
#    logset:logFormatInfo "filepattern=messages-<date:YYYYMMDD>$" ;
#    logset:logFormatInfo "filepattern=messages$" ;
#    logset:logFormatInfo "ts_words=1" ;
#    logset:logFormatInfo "part_word=2" ;

import rdflib
import LogsGraph


from collections import namedtuple
FileInfo = namedtuple('FileInfo', 'base, relpath, filename')

from Typing import Set, Tuple, List, Dict
FileInfoSet = Set[FileOnfo]
# when cataloging a dataset, LogSeries.candiates() takes
# a set of files (each described by a FileInfo tuple) and returns
# two sets: the files (or whatever) that are probably part 
# of this LogSeries and the remaining ones that are not
# We return two sets because a LogSeries might consume 
# candidate files but return a candidate directory instead
# (eg for FilePerTimePoint)
SplitFileInfoSet = Tuple[FileInfoSet, FileInfoSet] # candiates, remaining

from LogFormatType import LogFormatType
from LogClass import LogClass
class LogSeries(LogClass):

    rdf_class = "logset:LogSeries"

    # each class should define this map of predicate to attribute name (eg:
    #    "dct:title": "title"
    predicates = { "logset:infoType":      "infotype",
                   "logset:logFormatType": "logfmt_type" 
                   "logset:logFormatInfo": "fmtinfo"
                 }

    # logseries (or perhaps, the specific LogFormatTypes) should have a 
    # list of logFormatInfo keys that it knows what to do with
    #
    # one type of formatinfo is how to get the subject:
    # logFormatInfo "subjectIdentifier=filepattern"
    # logFormatInfo "subjectIdentifier=ask:series"
    # logFormatInfo "subjectIdentifier=ask:log"
    # logFormatInfo "subjectIdentifier=inspect"
    # 
    # and specificSubjectPattern?
    # this is what gets set if the identified subject is too fine-grained to
    # be a node in the graph (eg a single link). Probably this mostly won't 
    # get used...

    def _init(self):
        self._fmtinfo:      List[str]     = None
        self._fmtinfo_dict: Dict[str,str] = None
        self._filepatterns: Set[str]      = None
        self._logfmt_type:  LogFormatType = None

    def _populate_fmtinfo(self):
        # used internally by getters for fmtinfo and fmtinfo_dict.
        # Since no fmtinfo was provided at instantiation, assume we can 
        # get it from the graph (ie it is already there)
        self._fmtinfo = []
        self._fmtinfo_dict = {}
        subj = rdflib.term.URIRef(self.uri)
        logset = LogsGraph.getns('logset')
        pred = logset['logFormatInfo']
        for entry in LogsGraph.graph.objects(subj, pred):
            obj = str(entry)
            self._fmtinfo.apend(obj)
            key, sep, value = obj.partition('=')
            # fmtinfo_dict is actually a dict of lists, since keys 
            # within it can also be repeated:
            value_list = self._fmtinfo_dict.get(key, [])
            value_list.append(value)

    @property
    def fmtinfo(self) -> List[str]:
        if self._fmtinfo is None:
            self._populate_fmtinfo()
        return list(self._fmtinfo)

    @fmtinfo.setter
    def fmtinfo(self, value: List[str]):
        self._fmtinfo = value
        self._fmtinfo.append
        
    @property
    def fmtinfo_dict(self):
        if self._fmtinfo_dict is None:
            self._populate_fmtinfo()
        return self._fmtinfo_dict

    @property
    def logfmt_type(self) -> str:
        if self._logfmt_type is None:
            subj = rdflib.term.URIRef(self.uri)
            logset = LogsGraph.getns('logset')
            pred = logset['logFormatType']
            # there should be exacly 1 fmttype:
            self._logfmt_type = str(next(LogsGraph.graph.objects(subj, pred), None))
        return self._logfmt_type


    def candidates(self, files: FileInfoSet) -> SplitFileInfoSet:
        if self._filepatterns is None:
            # find filepatterns in the fmtinfo_dict and translate the 
            # user-friendly tags into valid regexs:
            tags = re.compile('(<[\w:]+>)')
            self._filepatterns = set()
            for filepattern in self.fmtinfo_dict.get('filepattern', []):
                parts = tags.split(filepattern)
                # every 2nd part will be a tag, replace it with corresponding pattern
                tagpatterns = [ pattern_for_tag(t) for t in parts[1::2] ]
                fp = ''.join(sum(zip(parts[:-1:2],tagpatterns),())) + parts[-1]
                self._filepatterns.add(fp)
        # now filter the set_of_fileinfos for ones matching a filepattern:
        candidates = set()
        for pattern in sorted(self._filepatterns, ley=len, reverse=True):
            regex = re.compile(pattern)
            candidates += set(filter(lambda x: regex.match(x.filename), set_of_fileinfos))
        remaining = files - candidates
        # TODO the following chunk should be handled by passing to the logFormatType
        # object to further filter the candidate list according to what it knows 
        # (ie, the knowledge is in the LogFormatType/handler objects not the 
        # LogSeries object)
        # handler = LogFormatType.handler(self.logfmt_type)
        # mine, not_mine = handler.filter_candidates(candidates)
        # remaining += not_mine
        # return (mine, remaining)
        #
        # check the mimetype, if it is inode/directory then the candidates are 
        # the directories with files matching this, but the matching files 
        # should be removed from the candidates_remaining list
        mediatype = self.properties.get("dcat:mediaType", None)
        if mediatype is None:
            # try to get it from the graph:
            subj = rdflib.term.URIRef(self.uri)
            logset = LogsGraph.getns('logset')
            pred = logset['logFormatType']
            # there should be exacly 1 fmttype:
            fmttype = next(LogsGraph.graph.objects(subj, pred), None)
            if fmttype is not None:
                pred = LogsGraph.getns('dcat')['mediaType']
                mediatype = next(LogsGraph.graph.objects(fmttype, pred), None)
                self.properties["dcat:mediaType"] = mediatype
        if mediatype is not None:
            if mediaType == 'inode/directory':
                keep = set()
                while len(candidates)>0:
                    sample = candidates.pop()
                    d = sample.relpath # the directory that will become a returned candidate
                    f = set(filter(lambda x: x.relpath==d, candidates))
                    relpath, sep, fname = d.rpartition(os.sep)
                    keep.add(FileInfo(sample.base, relpath, fname))
                    candidates -= f
                return (keep, remaining)
            else:
                # finally, only accept candidates with correct mimetype
                test = lambda x: mediatype != magic.from_file(os.sep.join(x), mime=True)
                wrongtype = set(filter(test, candidates))
                candidates -= wrongtype
                remaining += wrongtype
                return (candidates, remaining)

# keep a dict of known logseries (by name):
_known_logseries = None
from typing import Generator
def known_logseries() -> Generator[LogSeries, None, None]:
    global _known_logseries
    if _known_logseries is None:
        _known_logseries = {}
        q = ''' select ?uri ?infotype ?fmttype ?mediatype WHERE {
                  ?uri a logset:LogSeries .
                  ?uri logset:logInfoType ?infotype .
                  ?uri logset:logFormatType ?fmttype .
                  OPTIONAL { ?fmttype dcat:mediaType ?mediatype } .
                }
            '''
        fields = [ None, "logset:infoType", "logset:logFormatType", "dcat:mediaType" ]
        for row in LogsGraph.graph.query(q):
            uri = str(row[0])
            props = { fields[i]: str(row[i]) for i in range(1,len(row)) }
            logseries = LogSeries(uri=uri, properties=props)
            _known_logseries[logseries.name] = logseries
    for name in _known_logseries:
        yield _known_logseries[name]

from typing import Pattern
_pattern_for_tag = None
def pattern_for_tag(tag: str) -> str:
    """ return the regex pattern corresponding to a tag """
    global _pattern_for_tag
    if _pattern_for_tag is None:
        # TODO: anytime a new tag is recorded, we need to add it!
        q = ''' SELECT ?tag ?regex_pattern WHERE {
                 ?id a logset:FilenamePattern .
                 ?id logset:tag ?tag .
                 ?id logset:regex ?regex_pattern .
            } '''
        for row in LogsGraph.graph.query(q):
            _pattern_for_tag[str(row[0])] = str(row[1])
    return _pattern_for_tag[tag]


#--------
# keep a dict of known logseries (by name):
#_known_logseries = None
#def known_logseries():
#    global _known_logseries
#    if _known_logseries is None:
#        _known_logseries = {}
#        q = ''' select ?uri ?infotype ?fmttype ?mediatype WHERE {
#                  ?uri a logset:LogSeries .
#                  ?uri logset:logInfoType ?infotype .
#                  ?uri logset:logFormatType ?fmttype .
#                  OPTIONAL { ?fmttype dcat:mediaType ?mediatype } .
#                }
#            '''
#        for row in LogsGraph.graph.query(q):
#            uri, infotype, fmttype, mediatype = (str(i) for i in row)
#            logseries = LogSeries(uri=uri, infotype=infotype, 
#                                  fmttype=fmttype, mediatype=mediatype)
#            _known_logseries[logseries.name] = logseries
#    for name in _known_logseries:
#        yield _known_logseries[name]
#
#from typing import Pattern
#_pattern_for_tag = None
#def pattern_for_tag(tag: str) -> str:
#    """ return the regex pattern corresponding to a tag """
#    global _pattern_for_tag
#    if _pattern_for_tag is None:
#        # TODO: anytime a new tag is redorded, we need to add it!
#        q = ''' SELECT ?tag ?regex_pattern WHERE {
#                 ?id a logset:FilenamePattern .
#                 ?id logset:tag ?tag .
#                 ?id logset:regex ?regex_pattern .
#            } '''
#        for row in LogsGraph.graph.query(q):
#            _pattern_for_tag[str(row[0])] = str(row[1])
#    return _pattern_for_tag[tag]
#import magic # requires python-magic (pip install --user python-magic)
#
#from collections import namedtuple
#FileInfo = namedtuple('FileInfo', 'base, relpath, filename')
#from typing import Set, List, Dict
#FileInfoSet = Set[FileInfo]
#ListOfStrings = List[str]
#SetOfStrings = Set[str]
#FmtInfoDict = Dict[str,ListOfStrings]
#
#class LogSeries:
#    """ object corresponding to a logset:LogSeries """
#
#    def __init__(self, uri: str, infotype: str, fmttype:str, mediatype:str=None,
#                 fmtinfo: FmtInfoDict = None, filepatterns: SetOfStrings = None):
#        self.uri = uri
#        self.name = uri.rpartition('#')[2]
#        self.infotype = infotype
#        self.fmttype = fmttype
#        self.mediatype = mediatype # actually corresponds to mediatype of logFormatType
#        self._fmtinfo = None # dict of key: list-of-values eg filepattern: [fp1, fp2,...]
#        self._filepatterns = None # set() of regex strings
#
#    # FIXME problem: how to map the file to the filepattern regex, so that handlers can extract
#    # metadata from it (eg esp filepertimepoint)?
#    # hmm, would implementing this asa generator work? (then catalog iterates over candidate sets?)
#    def candidate_files(self, set_of_fileinfos: FileInfoSet) -> FileInfoSet:
#        if self._fmtinfo is None:
#            self._fmtinfo = {} # key: list-of-values
#            # this assumes the logseries is already in the graph:
#            subject = rdflib.term.URIRef(self.uri)
#            logset = LogsGraph.getns('logset')
#            predicate = logset['logFormatInfo']
#            for entry in LogsGraph.graph.objects(subject, predicate):
#                key, sep, value = str(entry).partition('=')
#                infolist = self._fmtinfo.get(key, [])
#                infolist.append(value)
#        if self._filepatterns is None:
#            # now translate the filepatterns into an ordered list of regexes:
#            tags = re.compile('(<[\w:]+>)')
#            self._filepatterns = set()
#            for filepattern in self._fmtinfo.get('filepattern', []):
#                parts = tags.split(filepattern)
#                # every 2nd part will be a tag, replace it with corresponding pattern
#                tagpatterns = [ pattern_for_tag(t) for t in parts[1::2] ]
#                self._filepatterns.add(''.join(sum(zip(parts[:-1:2],tagpatterns),())) + parts[-1])
#        # now filter the set_of_fileinfos for ones matching a filepattern:
#        candidates = set()
#        for pattern in sorted(self._filepatterns, ley=len, reverse=True):
#            regex = re.compile(pattern)
#            candidates += set(filter(lambda x: regex.match(x.filename), set_of_fileinfos))
#        if self.mediatype is not None:
#            # finally, only accept candidates with correct mimetype 
#            test = lambda x: self.mediatype == magic.from_file(os.sep.join(x), mime=True)
#            candidates = filter(test, candidates)
#        return candidates
#
#    # logFormatType might be a file, or might be eg localCommands, newtAPI, ..
#    # the logseries has the logFormatType, so should probably be responsible for
#    # instantiating ConcreteLog instances (and passing them an accessor class)
#    # the accessor/handler factory needs the logformattype, url .. and other info? yes
#    # .. so only the url comes from the concretelog itself
#    def concreteLog(self, fileinfo: FileInfo) -> ConcreteLog:
#        """ instantiate the concretelog based on the appropriate handler """
#        fullpath = os.sep.join(fileinfo)
#        
#        pass
                 
        

# --------
#
#
#from typing import Pattern
#_pattern_for_tag = None
#_regex_for_filepattern = None
#def find_logseries(pattern: Pattern) -> LogSeries:
#    # tags like <time:HHMMss> and corresponding regex patterns,
#    # are common to any LogSeries filename pattern:
#    global _pattern_for_tag
#    if _pattern_for_tag is None:
#        # TODO: anytime a new tag is redorded, we need to add it!
#        q = ''' SELECT ?tag ?regex_pattern WHERE {
#                 ?id a logset:FilenamePattern .
#                 ?id logset:tag ?tag .
#                 ?id logset:regex ?regex_pattern .
#            } '''
#        for row in LogsGraph.graph.query(q):
#            tag = str(row[0])
#            pattern = str(row[1])
#            _pattern_for_tag[tag] = pattern
#    # filename patterns may incorporate tags, and are specific to a LogSeries:
#    global _regex_for_filepattern:
#
#
## utilities needed to identify the appropriate logseries given a 
## file pattern:
#_pattern_tag_regexs = {}    # tag: regex_pattern
#_logseries_for_pattern = {} # pattern (str): LogSeries
#def 
#
#def known_filename_patterns(graph: graph: rdflib.Graph):
#    """ iterate over """
#    query = '''SELECT ?tag ?regex WHERE {
#                ?id a logset:FilenamePattern .
#                ?id logset:tag ?tag .
#                ?id logset:regex ?regex .
#            }'''
#    global _filenamepatterns
#    for row in graph.query(query):
#        _filenamepatterns[str(row[0])] = str(row[1])
#
#_logseries = {} # label: LogSeries
#def 
#
#
#from typing import Pattern
#import re
#def logseries_for_filename_pattern(pattern: Pattern):
#    """ return the logseries associated with a filename pattern """
#
#    
#class LogSeries:
#    """ object corresponding to a logset:LogSeries """
#
#    # rdf predicates corresponding to object attributes:
#    _predicates = {'logset:infoType': 'infoTypes',
#    _predicates = {'logset:infoType': 'infoTypes',
#                   
#
#    def __init__(self, graph: rdflib.Graph, uri: str = None, 
#                 namespace: str = None, label: str = None,
#                 **properties: rdflib.Term.Identifier): 
#        """ a LogSeries is either in a graph, or needs to be described and 
#            added to one
#        """
#        assert( not (uri is None and (namespace is None or label is None)) )
#        self._graph = graph
#        if uri is None:
#            if namespace is None:
#                raise Exception("need either a uri, or a namespace and optional label") 
#            
#
#        self.uri = uri
#        ns,sep,label = uri.rpartition('#')
#        self.namespace = rdflib.Namespace(ns+sep)
#        if label == '':
#            label = ran_str(8)
#        self.label = label
#        self.prefix = label
#
#    def candidates(self, 
#
