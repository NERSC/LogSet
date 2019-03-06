#!/usr/bin/env python3

import logging
import sys
logging.debug(str(sys.version_info))
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

from typing import Iterable, Dict, Any
from collections.abc import Mapping
class Context(Mapping):
    """ A dict-of-stacks: when adding/setting a key-value pair, the value is
        pushed to a stack rather than overwriting the current value. And when 
        reading a value, Context returns the item on the top of the stack. 
        Setting values other than via push is not supported, and values can 
        be reverted to their previous value with pop
    """
    def __init__(self, *args, **kwargs):
        for arg in args:
            if arg is None:
                self._storage = dict()
            elif isinstance(arg, Context):
                self._storage = dict()
                # this needs to be a deep-ish copy so that each stack in
                # _storage is copied, not just the _storage dict:
                for key,stack in arg._storage.items():
                    self._storage[key] = list(stack) 
            elif isinstance(arg, dict):
                self._storage = { key: [ arg[key] ] for key in arg }
            else:
                self._storage = { pair[0]: [ pair[1] ] for pair in arg }
            break
        else:
            # a bunch of key=value arguments:
            self._storage = { key: [ value ] for key,value in kwargs.items() }

    def __getitem__(self, key):
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

    def __len__(self):
        return len(self._storage)

    def __str__(self):
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

    def pop(self, keys:Iterable):
        retval = []
        for key in keys:
            retval.append(self._storage[key].pop())
            if len(self._storage[key])==0:
                del(self._storage[key])
        return tuple(retval)


import unittest
class TestContext(unittest.TestCase):
            
    def test_create_from_list(self):
        letters = 'abcdefg'
        l = [ (i, letters[i]) for i in range(len(letters)) ] 
        c = Context(l)
        for i in range(len(letters)):
            self.assertEqual(c[i],letters[i])

    def test_create_from_dict(self):
        letters = 'abcdefg'
        d = { i: letters[i] for i in range(len(letters)) } 
        c = Context(d)
        for i in range(len(letters)):
            self.assertEqual(c[i],letters[i])

    def test_create_from_kwargs(self):
        c = Context(this=1, that=2, the_other=3)
        self.assertEqual(c['this'], 1)

    def test_create_from_context(self):
        letters = 'abcdefg'
        l = [ (letters[i], i) for i in range(len(letters)) ] 
        c1 = Context(l)

        c2 = Context(c1)
        self.assert_looks_equal(c1,c2)

        c2.push(a=99, b=111)
        self.assert_looks_different(c1,c2)
        #print(c1)
        #print(c2)
        #self.assertNotEqual(c1['a'], c2['a'])
        #self.assertNotEqual(c1['b'], c2['b'])

    def test_create_empty(self):
        c1 = Context()
        c2 = Context(None)

    def test_push_and_pop(self):
        letters = 'abcdefg'
        l = [ (letters[i], i) for i in range(len(letters)) ] 
        c1 = Context(l)
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
        letters = 'abcdefg'
        l = [ (letters[i], i) for i in range(len(letters)) ] 
        c1 = Context(l)
        self.assertTrue(c1.get('d', None) == 3)
        self.assertTrue(c1.get('k', None) is None)

    def test_cannot_directly_set(self):
        letters = 'abcdefg'
        l = [ (letters[i], i) for i in range(len(letters)) ] 
        c1 = Context(l)
        def try_setting(ctx, key, val):
            ctx[key] = val
        self.assertRaises(TypeError, try_setting, c1, 'k', 99) 


    # some utility functions for comparing contexts:
    def assert_looks_equal(self, c1, c2):
        for i in c1:
            self.assertEqual(c1[i], c2[i])
        for i in c2:
            self.assertEqual(c1[i], c2[i])

    def assert_looks_different(self, c1, c2):
        equal = True
        for i in c1:
            equal = equal and c1[i]==c2[i]
        for i in c2:
            equal = equal and c1[i]==c2[i]
        self.assertFalse(equal)


if __name__ == '__main__':
    unittest.main()
 


