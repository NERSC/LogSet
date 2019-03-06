#!/usr/bin/env python3

import logging
import sys
logging.debug(str(sys.version_info))
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

# could conceivably access files over ssh/scp this way too..

import re
import os
_protocols = ['http', 'https', 'file']
_pattern = '|'.join(( '(?P<{0}>{0}:)'.format(p) for p in _protocols ))
_re_url = re.compile('(?:{})(?P<path>.*)'.format(_pattern))
def factory(url):
    m = _re_url.search(url)
    if m is None:
        cls = LocalTextFile
        path = url
    elif m.group('file'):
        cls = LocalTextFile
        path = m.group('path')
    else:
        cls = RemoteTextFile
        path = url
    return cls(path)

# common interface for local and remote files:

class TextFile:
    """ common interface for accessing local and remote files """
    _blksz = 4096 # somewhat-arbitrary chunksize as unit for reading

    @property
    def nblocks(self):
        return (self.size+self._blksz-1) // self._blksz


class LocalTextFile(TextFile):

    def __init__(self, path):
        self.path = path
        self._size = None
        self._lastlines_cache = {} # block: partial-line

    @property
    def size(self):
        if self._size is None:
             self._size = os.path.getsize(self.path)
        return self._size

    #def readlines(self, firstblock=0, n=0):
    def readlines(self, start=0, n=0):
        """ generator yiedling n lines starting from the first definitely-
            complete line after start. If start!=0, readlines assumes
            it has landed partway into a line and discards until the next line 
            break. If there is less than a full line, yields no lines
            If n<=0. read to the end of the file
        """
        #logging.info("reading {0:d} lines from {1:d}".format(n,start))
        with open(self.path, 'r') as f:
            #f.seek(firstblock*self._blksz)
            f.seek(start) 
            line = f.readline()
            #logging.info("read a line: {0}".format(line))
            count=0
            if start == 0:
                count += 1
                #logging.info("yielding: {0}".format(line))
                yield line
            while count < n or n <= 0:
                line = f.readline()
                if line == '':
                    break
                count += 1
                #logging.info("yielding: {0}".format(line))
                yield line


class RemoteTextFile(TextFile):

    def __init__(self, url):
        self.url = url
        self._size = None
        # TODO: implement this:
        self._lastlines_cache = {} # block: partial-line

    @property
    def size(self):
        if self._size is None:
            with urllib.request.urlopen(self.url) as f:
                self._size = int(f.info()["Content-Length"])
        return self._size

    def readlines(self, start=0, n=0):
        if start==0 and n<=0:
            # read whole file:
            with urllib.request.urlopen(self.url) as f:
                for line in f.readlines():
                    yield line
        else:
            line = ''
            while count < n or n < 0:
                # need to keep fetching blocks till we have enough lines
                #bs = min(self._blksz, self.size)
                #b = 'bytes={0:d}-'.format(firstblock*self._blksz)
                b = 'bytes={0:d}-'.format(start)
                if n>0: # not reading till end of file
                    b+='{0:d}'.format(min(start+self._blksz,self.size))
                    #b+='{0:d}'.format((firstblock+1)*self._blksz - 1)
                req = urllib.request.Request(self.url, headers={'Range':b})
                with urllib.request.urlopen(req) as f:
                    line += f.readline() # in case previous range left unfinished line
                    while count < n or n < 0:
                        if line[-1] != '\n':
                            # end of block, break and read next block
                            #firstblock += 1 
                            start += self._blksz
                            break
                        n += 1
                        yield line
                        line = f.readline()


#import re
#protocols = ['http', 'https', 'file']
#pattern = '|'.join(( '(?P<{0}>{0}:)'.format(p) for p in protocols ))
#re_url = re.compile('(?:{})(?P<path>.*)'.format(pattern))
#def TimeStampedLogFile(url, info):
#    m = re_url.search(url)
#    if m is None:
#        cls = LocalTimeStampedLogFile
#        path = url
#    elif m.group('file'):
#        cls = LocalTimeStampedLogFile
#        path = m.group('path')
#    else:
#        cls = RemoteTimeStampedLogFile
#        path = url
#    return cls(path, info)
#
#logFormat = 'timeStampedLogFile'
#constructor = TimeStampedLogFile
#
#import os
#import dateutil.parser
#class LocalTimeStampedLogFile(LogFormatType):
#    # logfiles might be very large, and we often need to find particular lines.
#    # rather than reading the whole file linearly and parsing for newlines, we'll
#    # read chunks from an arbitrary location and pull complete lines from them.
#    # _blocksz is an initial chunk size to use for this
#    _blocksz = 1000
#
#    def __init__(self, path, info):
#        self.path = path
#        # regular attributes:
#        # ts_words is the word or word ranges making up the timestamp, 0 is first-word-in-line:
#        ts_words = info.get('ts_words',None)
#        if ts_words:
#            first, sep, last = ts_words.partition('-')
#            ifirst = int(first)
#            if last:
#                ilast = int(last)+1
#            else:
#                ilast = ifirst + 1
#            self.ts_words = (ifirst,ilast)
#        else:
#            self.ts_words = None
#        # part_word is the word identifying the part about which each entry is:
#        part_word = info.get('part_word',None)
#        if part_word:
#            self.part_word = int(part_word)
#        else:
#            self.part_word = None
#        #for f in ('ts_words', 'part_word'):
#        #    setattr(self, f, int(info.get(f, None))) # TODO handle int conversion better
#        # attributes we might have to find from file:
#        for f in ('size', 't_start', 't_end'):
#            setattr(self, '_'+f, info.get(f, None))
#
#    @property
#    def size(self):
#        if self._size is None:
#             self._size = os.path.getsize(self.path)
#        return self._size
#
#    import io
#    def timespan(self):
#        """ return the timestamps of the first and last entries in the file """
#        if self._t_start is None or self._t_end is None:
#            with open(self.path, 'r') as f:
#                # find the first and last lines, check the timestamps
#                firstline = f.readline()
#            sz = self.size
#            #with open(self.path, 'rb') as f:
#            with open(self.path, 'r') as f: # must be text or string methods get confused
#                bs = min(self._blocksz, sz)
#                lines = []
#                while bs <= sz:
#                    #f.seek(-bs, 2)
#                    f.seek(sz-bs)   # can only seek from start in text files
#                    lines = f.readlines() # read to end of file
#                    if len(lines) > 1:
#                        break
#                    bs *= 2
#                else:
#                    raise Exception("can't find last entry in {0:s}".format(self.path))
#                lastline = lines[-1]
#            print (lastline)
#            print(lastline.split())
#            print(lastline.split()[self.ts_words[0]:self.ts_words[1]])
#            print(self.ts_words)
#            print(' '.join(lastline.split()[self.ts_words[0]:self.ts_words[1]]))
#            self._t_start = dateutil.parser.parse(' '.join(firstline.split()[self.ts_words[0]:self.ts_words[1]]))
#            self._t_end = dateutil.parser.parse(' '.join(lastline.split()[self.ts_words[0]:self.ts_words[1]]))
#        return (self._t_start, self._t_end)
#
#    def entries(self, since=None, until=None, parts=None):
#        """ return the log entries of data between 'since' (or the start of the 
#            file) and 'until' (or the end of the file), inclusive, optionally
#            filtering for certain parts
#        """
#        pass
#
#
#import urllib.request
#class RemoteTimeStampedLogFile(LogFormatType):
#    _blocksz = 1000
#
#    def __init__(self, url, info):
#        self.url = url
#        # regular attributes:
#        for f in ('ts_word', 'part_word'):
#            setattr(self, f, info.get(f, None))
#        # attributes we might have to find from file:
#        for f in ('size', 't_start', 't_end'):
#            setattr(self, '_'+f, info.get(f, None))
#
#    @property
#    def size(self):
#        if self._size is None:
#            with urllib.request.urlopen(self.url) as f:
#                self.size = f.info()["Content-Length"]
#        return self._size
#
#    def timespan(self):
#        if self._t_start is None or self._t_end is None:
#            with urllib.request.urlopen(self.url) as f:
#                # find the first and last lines, check the timestamps
#                firstline = f.readline()
#            # read the last _blocksz bytes
#            bs = min(self._blocksz, sz)
#            lines = []
#            # make sure we get at least a full line:
#            while bs <= sz:
#                b = 'bytes={0:d}-'.format(int(self.size)-bs)
#                req = urllib.request.Request(self.url, headers={'Range':b})
#                with urllib.request.urlopen(req) as f:
#                    lines = f.readlines() # read to end of file
#                    if len(lines) > 1:
#                        break
#                    bs += self._blocksz 
#            else:
#                raise Exception("can't find last entry in {0:s}".format(self.url))
#            lastline = lines[-1]
#            self._t_start = dateutil.parser.parse(firstline.split()[self.ts_word])
#            self._t_end = dateutil.parser.parse(lastline.split()[self.ts_word])
#        return (self._t_start, self._t_end)


    
