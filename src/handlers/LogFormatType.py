#!/usr/bin/env python3

class LogFormatType:
    """ base class and factory for objects that can handle logs of a 
        particular format. Subclasses should register themselves by 
        calling LogFormatType.register(Subclass, label), and clients should
        instantiate handler objects by calling 
        LogFormatType.factory(logfmt_uri, dict_of_logformatinfo)
        (note that "label" here is the iri, sans prefix)
    """
    pass
