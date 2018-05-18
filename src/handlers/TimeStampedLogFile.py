#!/usr/bin/env python3

import logging
import sys
logging.debug(str(sys.version_info))
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

#:timeStampedLogFile
#    a logset:LogFormatType ;
#    logset:dataSource :files ;
#    dcat:mediaType "text/plain" ;
#    .

#from graph.LogFormatType import FileBasedLogFormatType
#from FileBasedLogFormatType  import FileBasedLogFormatType
from util import MultiDict, ParseRule, cast
from . import TextFile
import re
from typing import Union, Generator
import dateutil.parser


#class TimeStampedLogFile(FileBasedLogFormatType):
class TimeStampedLogFile:
    rdf_class = "logset:timeStampedLogFile"

    # how to turn strings in fmtinfo into attributes we can use:
    fmtinfo_parsers = {
        'ts_words': ParseRule( re.compile('(?P<first>\d)(?:-(?P<last>\d))?'),
                               # make a tuple of (first,last):
                               lambda m: (cast(m,'first',int),cast(m,'last',int))),
        'part_word': ParseRule( re.compile('(?P<word>\d)'),
                               # just an integer:
                               lambda m: cast(m,'word',int))
                      }


    def __init__(self, target_url:str=None, fmtinfo:MultiDict=None):
#                 properties:MultiDict=None) -> None:
        """ constructor should take properties as a keyword argument
            (to pass to the Node superclass constructor). target_url
            (eg the file path to be opened) should be supported but
            not required (because Node factories might not provide it),
            same for fmtinfo
        """
        #super().__init__(properties=properties)
        self._size = None
        self._t_earliest = None
        self._t_latest = None
        self._actual_file = TextFile.factory(target_url)
        for attr,parserule in self.fmtinfo_parsers.items():
            if attr in fmtinfo:
                value = fmtinfo.one(attr)
                m = parserule.regex.search(value)
                setattr(self, attr, parserule.parser(m))
        self.filters = {}

    def _timestamp(self,words):
        first,last = self.ts_words
        last = last or first # in case it is none
        return ' '.join(words[first:last+1])

    def component(self,words):
        return words[part_word]
            
    @property 
    def size(self) -> int:
        """ the size in bytes """
        return self._actual_file.size

    @property 
    def t_earliest(self) -> str:
        """ the returned string should be parseable by python's
            dateutil.parser.parse
        """
        if self._t_earliest is None:
            line = next(self._actual_file.readlines(0,1))
            self._t_earliest = self._timestamp(line.split())
        return self._t_earliest
            
    @property 
    def t_latest(self) -> str:
        """ the returned string should be parseable by python's
            dateutil.parser.parse
        """
        if self._t_latest is None:
            latest = None
            # step backwards hrough the file in blocks until we 
            # have a complete line
            blksz = 1024
            start = min(0,self._actual_file.size - blksz)
            while start >= 0:
                for line in self._actual_file.readlines(start):
                    latest = line
                if latest is not None:
                    # we have a full line
                    break
            self._t_latest = self._timestamp(latest.split())
        return self._t_latest

#            nblocks=self._actual_file.nblocks
#            logging.info("nblocks is {0:d}".format(nblocks))
#            for i in range(1,nblocks+1):
#                for line in self._actual_file.readlines(nblocks-i,1):
#                    logging.info("read line {0}".format(line))
#                    latest = line
#                if latest is not None:
#                    break
#            logging.info("latest is {0}".format(latest))
#            self._t_latest = self._timestamp(latest.split())
#        return self._t_latest

    @property 
    def num_records(self) -> Union[int,None]:
        """ the number of records, if known/knowable, or None otherwise """
        return None
    
    def get_slice(self, since:str=None, until:str=None, 
                  limit:int=0) -> Generator[str,None,None]:
        """ find and yield records (in string form) from at or after 
            since (or start of file), and up until until= (or end of 
            file, inclusive), with an optional limit on the number of 
            records returned. since and until must be parseable by
            dateutil.parser.parse
        """
        t_earliest = dateutil.parser.parse(self.t_earliest)
        t_latest = dateutil.parser.parse(self.t_latest)
        tspan = (t_latest-t_earliest).total_seconds()
        # search for where to start reading
        if since is None:
            t_since = t_earliest
            start = 0
        else:
            t_since = dateutil.parser.parse(since)
        if until is None:
            t_until = t_latest
        else:
            t_until = dateutil.parser.parse(until)

        fullcount = 0 # number of read lines meeting time criteria
        count = 0     # number of lines actually yielded, after filters
        fraction = (t_since - t_earliest).total_seconds() / tspan
        fraction = max(fraction,0.0)
        start = int(self.size*fraction)
        while True:
            for line in self._actual_file.readlines(start):
                t_line = dateutil.parser.parse(self._timestamp(line.split()))
                if t_line < t_since:
                    # TODO is we're wildly short, break and jump forward
                    continue
                if fullcount == 0 and t_line > t_since:
                    # look back a bit
                    tspan = (t_line - t_earliest).total_seconds()
                    fraction = (t_since - t_earliest).total_seconds() / tspan
                    start = int(start*fraction)
                    start = max(0, start-1024) # back up a little more for good measure
                    break
                # line is after since
                if t_line > t_until:
                    break
                fullcount += 1
                # TODO apply filters
                count += 1
                yield line
                if limit>0 and limit<=count:
                    return # finished
            else:
                return # thats all we have
            if fullcount != 0:
                # we got here because we passed t_until
                return

    def set_filter(self, id_tag:str, field:str, regex:str, invert=False):
        """ add a filter to apply during get_slice. the id_tag is just 
            in support of clearing filters selectively (key in a dict).
            the field is a field name, eg "timestamp" - the available
            field names should be documented via the rdfs:comment property
            of the LogFormatType
        """
        pass
             
    def clear_filter(self, id_tag:str):
        """ remove the specified filter """
        pass

#import handlers
#handlers.register(TimeStampedLogFile)
#rdf_class = TimeStampedLogFile.rdf_class
#constructor = TimeStampedLogFile
