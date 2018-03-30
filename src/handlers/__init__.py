#!/usr/bin/env python3

__all__ = []
# borrowed from 
# https://stackoverflow.com/questions/14426574/how-to-import-members-of-modules-within-a-package/14428820#14428820
import os
globals_, locals_ = globals(), locals()
for filename in os.listdir(__name__):
    if filename[0] != '_' and filename.split('.')[-1] in ('py', 'pyw'):
        modulename = filename.split('.')[0]  # filename without extension
        package_module = '.'.join([__name__, modulename])
        module = __import__(package_module, globals_, locals_, [modulename])
        for name in module.__dict__:
            if not name.startswith('_'):
                globals_[name] = module.__dict__[name]
                __all__.append(name)
