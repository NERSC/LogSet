#!/usr/bin/env python3

# handler classes as still subclasses of Node (and more specifically, of 
# LogFormatType) but they must implement the following interface:
#
#     def __init__(self, target_url:str=None, fmtinfo:MultiDict=None,
#                  properties:MultiDict=None) -> None:
#         """ constructor should take properties as a keyword argument
#             (to pass to the Node superclass constructor). target_url
#             (eg the file path to be opened) should be supported but
#             not required (because Node factories might not provide it),
#             same for fmtinfo
#         """
#         super().__init__(properties=properties)
#
#     @property 
#     def t_earliest(self) -> str:
#         """ the returned string should be parseable by python's
#             dateutil.parser.parse
#         """
#
#     @property 
#     def t_latest(self) -> str:
#         """ the returned string should be parseable by python's
#             dateutil.parser.parse
#         """
#
#     @property 
#     def size(self) -> int:
#         """ the size in bytes """
#
#     @property 
#     def num_records(self) -> Union[int,None]:
#         """ the number of records, if known/knowable, or None otherwise """
#     
#     def get_slice(self, since:str=None, until:str=None, 
#                   limit:int=None) -> Generator[str,None,None]:
#         """ find and yield records (in string form) from at or after 
#             since (or start of file), and up until until= (or end of 
#             file, inclusive), with an optional limit on the number of 
#             records returned. since and until must be parseable by
#             dateutil.parser.parse
#         """
#
#     def set_filter(self, id_tag:str, field:str, regex:str, invert=False):
#         """ add a filter to apply during get_slice. the id_tag is just 
#             in support of clearing filters selectively (key in a dict).
#             the field is a field name, eg "timestamp" - the available
#             field names should be documented via the rdfs:comment property
#             of the LogFormatType
#         """
#              
#     def clear_filter(self, id_tag:str):
#         """ remove the specified filter """
#
_handler_interface = { 'rdf_class', 't_earliest', 't_latest', 'size', 
                       'num_records', 'get_slice', 'set_filter', 'clear_filter' } 

class UnsupportedLogFormatHandler(Exception):
    pass

from util import MultiDict
import re

_constructors = {} # rdf_class: specific LogFormatType
def factory(rdf_class:str, target_url:str, fmtinfo:MultiDict): 
#            properties:MultiDict=None):
    """ Factory to create suitable LogFormatType handler """
    # only use the suffix part, to make it easier to to convert between 
    # expanded uris and shorthand ones
    key = re.split('[:|#]',rdf_class)[-1]
    print(key)
    print(_constructors)
    print(rdf_class)
    print(target_url)
    print(fmtinfo)
    #print(properties)
    #raise Exception("what happened")
    #key = re.split('[:|#]',rdf_class)[-1]
    if key not in _constructors:
        raise UnsupportedLogFormatHandler(rdf_class)
    cls = _constructors[key]
    return cls(target_url, fmtinfo) #, properties=properties)

__all__ = [ UnsupportedLogFormatHandler, factory ]

def _find_handlers():
    # dynamically scan this directory for handler modules (plugin-style):
    # (borrowed and adapted from 
    # https://stackoverflow.com/questions/14426574/how-to-import-members-of-modules-within-a-package/14428820#14428820)
    from importlib import import_module
    import os
    import inspect
    this = os.path.dirname(os.path.abspath(__file__))
    packagename = this.rpartition(os.sep)[2] 
    globals_ = globals()
    for filename in os.listdir(this):
        if filename[0] != '_' and filename.split('.')[-1] in ('py', 'pyw'):
            modulename = filename.split('.')[0]  # filename without extension
            m = import_module('.' + modulename, package=packagename)
            for name in m.__dict__:
                if not name.startswith('_'):
                    thing = m.__dict__[name]
                    if inspect.isclass(thing) and _handler_interface <= set(thing.__dict__):
                        print("found class mplementing handler interface: " + str(thing.__dict__))
                        globals_[name] = thing
                        prefix,sep,key = thing.rdf_class.rpartition(':')
                        _constructors[key] = thing

_find_handlers()


# dynamically scan this directory for handler modules (plugin-style):
# (borrowed and adapted from 
# https://stackoverflow.com/questions/14426574/how-to-import-members-of-modules-within-a-package/14428820#14428820)
# handler modules must set module variables for rdf_class and constructor, eg:  
#      rdf_class = 'logset:TimeStampedLogfile'
#      constructor = TimeStampedLogfile

#from importlib import import_module
#import os
#this = os.path.dirname(os.path.abspath(__file__))
#for filename in os.listdir(this):
#    if filename[0] != '_' and filename.split('.')[-1] in ('py', 'pyw'):
#        modulename = filename.split('.')[0]  # filename without extension
#        m = import_module('.' + modulename, package='handlers')
#        if {'rdf_class', 'constructor'} <= set(m.__dict__):
#            constructors[m.rdf_class] = m.constructor
#
#def _import_modules():
#    # dynamically scan this directory for handler modules (plugin-style):
#    # (borrowed and adapted from 
#    # https://stackoverflow.com/questions/14426574/how-to-import-members-of-modules-within-a-package/14428820#14428820)
#    # handler modules must set module variables for logFormat and constructor, eg:  
#    #      logFormat = 'timeStampedLogfile'
#    #      constructor = TimeStampedLogfile
#    from importlib import import_module
#    import os
#    import inspect
#    this = os.path.dirname(os.path.abspath(__file__))
#    packagename = this.rpartition(os.sep)[2] 
#    globals_ = globals()
#    for filename in os.listdir(this):
#        if filename[0] != '_' and filename.split('.')[-1] in ('py', 'pyw'):
#            modulename = filename.split('.')[0]  # filename without extension
#            m = import_module('.' + modulename, package=packagename)
#            for name in m.__dict__:
#                if not name.startswith('_'):
#                    thing = m.__dict__[name]
#                    if inspect.isclass(thing) and _handler_interface <= set(thing.__dict__):
#                        print("found class mplementing handler interface: " + str(thing.__dict__))
#                        globals_[name] = thing
#                        _constructors[thing.rdf_class] = thing
#
#_import_modules()
#
##
##                    if not inspect.ismodule(thing):
##                        globals_[name] = thing
##                        __all__.append(name)
##                        if inspect.isclass(thing) and handler_interface <= set(thing.__dict__):
##                            constructors[thing.rdf_class] = thing
#
#
