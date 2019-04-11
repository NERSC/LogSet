#!/usr/bin/env python3

import typing as t
import types

from . import info

commands: t.Dict[str,types.ModuleType] = {
    'info': info
}

