#!/usr/bin/env python3

import typing as t
import types

from . import info
from . import use
from . import query

commands: t.Dict[str,types.ModuleType] = {
    'info': info,
    'use': use,
    'query': query,
}

