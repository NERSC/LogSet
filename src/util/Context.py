#!/usr/bin/env python3

import sys
if sys.version_info < (3,5):
    raise Exception("Requires python 3.5+")

import logging

from typing import Iterable, Dict, Any, Tuple, Mapping
#from collections.abc import Mapping
class Context(Mapping):
    """ A dict-of-stacks: when adding/setting a key-value pair, the value is
        pushed to a stack rather than overwriting the current value. And when 
        reading a value, Context returns the item on the top of the stack. 
        Setting values other than via push is not supported, and values can 
        be reverted to their previous value with pop.
        The idea is that something can pass a context of "my own context plus 
        these specifics" by pushing the specifics onto the context, and 
        popping them off afterwards
        A Context can be created from a Mapping (including another Context),
        and all keys should be strings
    """
    _storage: Dict[str,Any]
    def __init__(self, _source: Mapping[str,Any] = {}, **kwargs: Any):
        if _source:
            if isinstance(_source, Context):
                # semi-deep copy: copy each stack in _storage
                self._storage = { 
                    key: list(stack) for key,stack in _source._storage.items() 
                }
            else:
                # make a stack for each item in the incoming dict/Mapping
                self._storage = { key: [ _source[key] ] for key in _source }
        else:
            # a bunch of key=value arguments:
            self._storage = { key: [ value ] for key,value in kwargs.items() }

    def __getitem__(self, key) -> Any:
        # look at top of stack
        return self._storage[key][-1]

    def get(self, key, default=None) -> Any:
        try:
            return self._storage[key][-1]
        except KeyError:
            return default

    def __iter__(self):
        # iterates through keys, so no change from basic dict
        return iter(self._storage) 

    def __len__(self) -> int:
        # number of stacks, no information about depth
        return len(self._storage)

    def __str__(self) -> str:
        return str(self._storage)

    def push(self, *args:Dict, **kwargs):
        """ takes either one dict-like thing, or a bunch of key=value args """
        for arg in args:
            items = arg.items()
            break
        else:
            items = kwargs.items()

        for key, value in items:
            if key not in self._storage:
                self._storage[key] = []
            self._storage[key].append(value)

    def pop(self, keys:Iterable) -> Tuple:
        retval = tuple(self._storage[key].pop() for key in keys)
        # clean up any empty stacks:
        for key in keys:
            if not self._storage[key]:
                del(self._storage[key])
        return retval


import unittest
class TestContext(unittest.TestCase):

    def test_create_from_dict(self):
        d = { l: i for i,l in enumerate('abcdefg') }  
        c = Context(d)
        for key in d:
            self.assertEqual(d[key], c[key])

    def test_create_from_kwargs(self):
        c = Context(this=1, that=2, the_other=3)
        self.assertEqual(c['that'], 2)

    def test_create_from_context(self):
        c1 = Context({ l: i for i,l in enumerate('abcdefg') })
        c2 = Context(c1)
        self.assert_looks_equal(c1,c2)

        c2.push(a=99, b=111)
        self.assert_looks_different(c1,c2)

    def test_create_empty(self):
        c1 = Context()
        assert len(c1)==0
        assert not c1

    def test_push_and_pop(self):
        c1 = Context({ l: i for i,l in enumerate('abcdefg') })
        c2 = Context(c1)

        c2.push(a=99, b=111)
        self.assertNotEqual(c1['a'], c2['a'])
        self.assertNotEqual(c1['b'], c2['b'])
        c2.pop(('a','b'))
        self.assert_looks_equal(c1,c2)

        some_properties = {'a':'a string', 'b':51}
        c2.push(some_properties)
        self.assert_looks_different(c1,c2)
        self.assertEqual(c2['b'], 51)
        c2.pop(some_properties)
        self.assert_looks_equal(c1,c2)


    def test_get(self):
        c1 = Context({ l: i for i,l in enumerate('abcdefg') })
        self.assertTrue(c1.get('d', None) == 3)
        self.assertTrue(c1.get('k', None) is None)
        self.assertTrue(c1.get('k', 3) == 3)

    def test_cannot_directly_set(self):
        c1 = Context({ l: i for i,l in enumerate('abcdefg') })
        def try_setting(ctx, key, val):
            ctx[key] = val
        self.assertRaises(TypeError, try_setting, c1, 'k', 99) 


    # some utility functions for comparing contexts:
    def assert_looks_equal(self, c1, c2):
        for key in c1:
            self.assertEqual(c1[key], c2[key])
        for key in c2:
            self.assertEqual(c1[key], c2[key])

    def assert_looks_different(self, c1, c2):
        equal = True
        for key in c1:
            equal = equal and c1[key]==c2[key]
        for key in c2:
            equal = equal and c1[key]==c2[key]
        self.assertFalse(equal)


if __name__ == '__main__':
    unittest.main()
 


