#!/usr/bin/env python3

class UnsupportedLogFormatHandler(Exception):
    pass

constructors = {} # logFormat: LogFormatType
def factory(logFormat, url, info):
    """ Factory to create suitable LogFormatType """
    try:
        handler = constructors[logFormat](url, info)
    except KeyError:
        raise UnsupportedLogFormatHandler()
    return handler

__all__ = [ UnsupportedLogFormatHandler, factory ]

# dynamically scan this directory for handler modules (plugin-style):
# (borrowed and adapted from 
# https://stackoverflow.com/questions/14426574/how-to-import-members-of-modules-within-a-package/14428820#14428820)
# handler modules must set module variables for logFormat and constructor, eg:  
#      logFormat = 'timeStampedLogfile'
#      constructor = TimeStampedLogfile
from importlib import import_module
import os
this = os.path.dirname(os.path.abspath(__file__))
#for filename in os.listdir(__name__):
for filename in os.listdir(this):
    if filename[0] != '_' and filename.split('.')[-1] in ('py', 'pyw'):
        modulename = filename.split('.')[0]  # filename without extension
        m = import_module('.' + modulename, package='handlers')
        if {'logFormat', 'constructor'} <= set(m.__dict__):
            constructors[m.logFormat] = m.constructor

