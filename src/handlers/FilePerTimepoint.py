#!/usr/bin/env python3

# system python 3 on Cori is broken so user will need to load a
# python module, which will be 3.6+ anyway, so we'll take advantage
# of some of python's modern features:
import sys
print(sys.version_info)
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+ .. try:\n  module load python/3.6-anaconda-4.4")

from .LogFormatType import LogFormatType

import os
import datetime
class FilePerTimepoint(LogFormatType):

    def __init__(self, path, info):
        self.path = path
        # attributes we might have to find from file:
        for f in ('size', 't_start', 't_end'):
            setattr(self, '_'+f, info.get(f, None))
        # keep the info dict in case we need more from it:
        self.info = info

    @property
    def size(self):
        if self._size is None:
             self._size = os.path.getsize(self.path)
        return self._size

    def timespan(self):
        if self._t_start is None or self._t_end is None:
            # each file in a FilePerTimepoint corresponds with a single time point, 
            # ie the startDate and endDate are the same.
            # Use the filename regex to find a date stamp:
            regex = self.info['fileregex']
            #print (regex)
            #print (self.path)
            m = regex.search(self.path)
            if m:
                #print (m.groups())
                year = int(m.group('year'))
                month = int(m.group('month'))
                day = int(m.group('day'))
                hour = int(m.group('hour'))
                minute = int(m.group('minute'))
                second = int(m.group('second'))
                self._t_start = datetime.datetime(year,month,day,hour,minute,second)
                self._t_end = self._t_start
        return (self._t_start, self._t_end)

logFormat = 'filePerTimepoint'
constructor = FilePerTimepoint

