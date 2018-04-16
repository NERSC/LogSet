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
import dateutil
class UnstructuredFile(LogFormatType):

    def __init__(self, path, info):
        self.path = path
        # attributes we might have to find from file:
        for f in ('size', 't_start', 't_end'):
            setattr(self, '_'+f, info.get(f, None))

    @property
    def size(self):
        if self._size is None:
             self._size = os.path.getsize(self.path)
        return self._size

    def timespan(self):
        # for now:
        return (None, None)

logFormat = 'unstructuredFile'
constructor = UnstructuredFile

