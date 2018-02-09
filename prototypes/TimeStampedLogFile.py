#!/usr/bin/env python3

# logfiles might be very large, and we often need to find particular lines.
# rather than reading the whole file linearly and parsing for newlines, we'll
# read chunks from an arbitrary location and pull complete lines from them.
# _blocksz is an initial chunk size to use for this
_blocksz = 1000

import os
import dateutil
class TimeStampedLogFile:
    """ A logfile whose format is timestamped-entry-per-line """

    def __init__(self, name, rootpath=os.getcwd(), relpath='', tsword=0):
        self.name = name         # filename (only - no path components)
        self.rootpath = rootpath # where to start looking to open this file
        self.relpath = relpath   # path from rootpath o file
        self.tsword = tsword # which "word" in each line has the timestamp?

    def timespan(self):
        """ returns a tuple of first,last timestamp in file, in unix time """
        fullpath = os.path.join(self.rootpath, self.relpath, self.name)
        with open(fullpath, 'r') as f:
            firstline = f.readline()
        # find the last line in the file
        sz = os.path.getsize(fullpath)
        with open(fullpath, 'rb') as f:
            bs = min(_blocksz, sz)
            lines = []
            while bs <= sz:
                f.seek(-bs, 2)
                lines = f.readlines() # read to end of file
                if len(lines) > 1:
                    break
                bs *= 2
            else:
                raise Exception("can't find last entry in {0:s}".format(fullpath))
            lastline = lines[-1]
        first = dateutil.parser.parse(firstline.split()[self.tsword]).timestamp()
        last = dateutil.parser.parse(lastline.split()[self.tsword]).timestamp()
        return (first, last)

