#!/usr/bin/env python3

import logging
import sys
logging.debug(str(sys.version_info))
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

import random, string
def ran_str(length: int) -> str:
    """ produce a string of random letters, of a given length.
        Used to generate uri if one was not provided
    """
    return ''.join([random.choice(string.ascii_lowercase) for i in range(length)])

# for working with files found via os.walk:
from collections import namedtuple
FileInfo = namedtuple('FileInfo', 'base, relpath, filename')


ParseRule = namedtuple('ParseRule', 'regex, parser')
def cast(match, group, converter):
    """ given a re match object, identifier for a possibly-matched group
        and a conversion function, return a converted object. Eg, if:
          match = re.search('(?P<first>\d)(?:-(?P<last>\d))?','1-3')
          group = 'last'
          converter = int
        then cast(match, group, converter) == 3 
    """
    text = match.group(group)
    return converter(text) if text else None
