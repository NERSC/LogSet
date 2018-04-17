#!/usr/bin/env python3

# system python 3 on Cori is broken so user will need to load a
# python module, which will be 3.6+ anyway, so we'll take advantage
# of some of python's modern features:
import sys
print(sys.version_info)
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+ .. try:\n  module load python/3.6-anaconda-4.4")

from .LogFormatType import LogFormatType

# to get the timespan, and also to extract slices from a log, we need to 
# fetch arbitrary ranges from within the logfile. We can do this for local 
# files with seek, or remote files with urllib and range headers, but no
# method works for both. So we have two versions of the class and a factory
# method to instantiate the appropriate one:
import re
protocols = ['http', 'https', 'file']
pattern = '|'.join(( '(?P<{0}>{0}:)'.format(p) for p in protocols ))
re_url = re.compile('(?:{})(?P<path>.*)'.format(pattern))
def TimeStampedLogFile(url, info):
    m = re_url.search(url)
    if m is None:
        cls = LocalTimeStampedLogFile
        path = url
    elif m.group('file'):
        cls = LocalTimeStampedLogFile
        path = m.group('path')
    else:
        cls = RemoteTimeStampedLogFile
        path = url
    return cls(path, info)

logFormat = 'timeStampedLogFile'
constructor = TimeStampedLogFile

import os
import dateutil.parser
class LocalTimeStampedLogFile(LogFormatType):
    # logfiles might be very large, and we often need to find particular lines.
    # rather than reading the whole file linearly and parsing for newlines, we'll
    # read chunks from an arbitrary location and pull complete lines from them.
    # _blocksz is an initial chunk size to use for this
    _blocksz = 1000

    def __init__(self, path, info):
        self.path = path
        # regular attributes:
        # ts_words is the word or word ranges making up the timestamp, 0 is first-word-in-line:
        ts_words = info.get('ts_words',None)
        if ts_words:
            first, sep, last = ts_words.partition('-')
            ifirst = int(first)
            if last:
                ilast = int(last)+1
            else:
                ilast = ifirst + 1
            self.ts_words = (ifirst,ilast)
        else:
            self.ts_words = None
        # part_word is the word identifying the part about which each entry is:
        part_word = info.get('part_word',None)
        if part_word:
            self.part_word = int(part_word)
        else:
            self.part_word = None
        #for f in ('ts_words', 'part_word'):
        #    setattr(self, f, int(info.get(f, None))) # TODO handle int conversion better
        # attributes we might have to find from file:
        for f in ('size', 't_start', 't_end'):
            setattr(self, '_'+f, info.get(f, None))

    @property
    def size(self):
        if self._size is None:
             self._size = os.path.getsize(self.path)
        return self._size

    import io
    def timespan(self):
        """ return the timestamps of the first and last entries in the file """
        if self._t_start is None or self._t_end is None:
            with open(self.path, 'r') as f:
                # find the first and last lines, check the timestamps
                firstline = f.readline()
            sz = self.size
            #with open(self.path, 'rb') as f:
            with open(self.path, 'r') as f: # must be text or string methods get confused
                bs = min(self._blocksz, sz)
                lines = []
                while bs <= sz:
                    #f.seek(-bs, 2)
                    f.seek(sz-bs)   # can only seek from start in text files
                    lines = f.readlines() # read to end of file
                    if len(lines) > 1:
                        break
                    bs *= 2
                else:
                    raise Exception("can't find last entry in {0:s}".format(self.path))
                lastline = lines[-1]
            print (lastline)
            print(lastline.split())
            print(lastline.split()[self.ts_words[0]:self.ts_words[1]])
            print(self.ts_words)
            print(' '.join(lastline.split()[self.ts_words[0]:self.ts_words[1]]))
            self._t_start = dateutil.parser.parse(' '.join(firstline.split()[self.ts_words[0]:self.ts_words[1]]))
            self._t_end = dateutil.parser.parse(' '.join(lastline.split()[self.ts_words[0]:self.ts_words[1]]))
        return (self._t_start, self._t_end)

    def entries(self, since=None, until=None, parts=None):
        """ return the log entries of data between 'since' (or the start of the 
            file) and 'until' (or the end of the file), inclusive, optionally
            filtering for certain parts
        """
        pass


import urllib.request
class RemoteTimeStampedLogFile(LogFormatType):
    _blocksz = 1000

    def __init__(self, url, info):
        self.url = url
        # regular attributes:
        for f in ('ts_word', 'part_word'):
            setattr(self, f, info.get(f, None))
        # attributes we might have to find from file:
        for f in ('size', 't_start', 't_end'):
            setattr(self, '_'+f, info.get(f, None))

    @property
    def size(self):
        if self._size is None:
            with urllib.request.urlopen(self.url) as f:
                self.size = f.info()["Content-Length"]
        return self._size

    def timespan(self):
        if self._t_start is None or self._t_end is None:
            with urllib.request.urlopen(self.url) as f:
                # find the first and last lines, check the timestamps
                firstline = f.readline()
            # read the last _blocksz bytes
            bs = min(self._blocksz, sz)
            lines = []
            # make sure we get at least a full line:
            while bs <= sz:
                b = 'bytes={0:d}-'.format(int(self.size)-bs)
                req = urllib.request.Request(self.url, headers={'Range':b})
                with urllib.request.urlopen(req) as f:
                    lines = f.readlines() # read to end of file
                    if len(lines) > 1:
                        break
                    bs += self._blocksz 
            else:
                raise Exception("can't find last entry in {0:s}".format(self.url))
            lastline = lines[-1]
            self._t_start = dateutil.parser.parse(firstline.split()[self.ts_word])
            self._t_end = dateutil.parser.parse(lastline.split()[self.ts_word])
        return (self._t_start, self._t_end)

