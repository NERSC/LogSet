#!/usr/bin/env python3

import logging
import sys
logging.debug(str(sys.version_info))
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

class StringAsValuesWarning(Exception):
    def __init__(self,message=None):
        if message is None:
            message = "passing a string in place of a list of values will add"
            message += " each char as a separate value"
        self.message=message

import collections
from collections.abc import Mapping
import six
class MultiDict(Mapping):
    """ A MultiDict is a dictionary where each key maps to a set of values.
        Rather than setting an item like mydict['a'] = 12, you need to add it 
        like mydict.add('a', 12). If creating a MultiDict from a dict or 
        Iterable or via key/value arguments, then each value *must* be Iterable
    """
    def __init__(self, *args, **kwargs):
        #logging.debug("creating with args = {0} and kwargs = {1}".format(str(args),str(kwargs)))
        for arg in args:
            if arg is None:
                self._storage = dict()
            elif isinstance(arg, MultiDict):
                self._storage = dict()
                # this needs to be a deep-ish copy so that each stack in
                # _storage is copied, not just the _storage dict:
                for key,values in arg._storage.items():
                    self._storage[key] = set(values) 
            elif isinstance(arg, dict):
                # if the value is a string, set(arg[key]) will make a set of its letters, so
                # values in the dict need to be lists, not strings!
                #logging.debug("creating from a dict")
                #self._storage = dict()
                #for key,values in arg.items():
                #    logging.debug("key is " + str(key))
                #    logging.debug("value is " + str(value))
                #    self.add(key,value)
                self._storage = { key: set(arg[key])  for key in arg }
            else:
                self._storage = { pair[0]: set(pair[1]) for pair in arg }
                #self._storage = dict()
                #for pair in arg:
                #    self.add(pair[0],pair[1])
            break
        else:
            # a bunch of key=value arguments:
            self._storage = dict()
            for key, value in kwargs.items():
                #print("adding {0} = {1}".format(str(key), str(value)))
                self._storage[key] = set(value)
        #logging.debug("created as: " + str(self._storage))

    def __getitem__(self, key):
        """ returns a copy of the stored set, not the set itself """
        return set(self._storage[key])

    def __iter__(self):
        # iterates through keys, so no change from basic dict
        return iter(self._storage) 

    def __len__(self):
        return len(self._storage)

    def __str__(self):
        return str(self._storage)

    def one(self, key, default=None):
        """ return one (randomly selected) value from key. This is useful for
            entries that expect to only have one value
        """
        one = default
        values = self._storage.get(key, None)
        if values is not None and len(values)>0:
            one = next(iter(values))
        return one

    def add(self, key, *values):
        #logging.debug("adding {0} to {1}".format(str(values), str(key)))
        if key not in self._storage:
            self._storage[key] = set()
        #print(key)
        for v in values:
            #logging.debug("in add: key is " + str(key))
            #logging.debug("in add: value is " + str(v))
            self._storage[key].add(v)
        #logging.debug("now I have {0}".format(str(self._storage)))

    def add_values(self, key, values):
        """ add contents of an iterable """
        if key not in self._storage:
            self._storage[key] = set()
        if isinstance(values, six.string_types):
            raise StringAsValuesWarning()
        self._storage[key] |= set(values)

    def remove(self, key, *args):
        if len(args) == 0:
            del self._storage[key]
        else:
            #print("removing " +str(set(args)))
            self._storage[key] -= set(args)


import unittest
class TestMultiDict(unittest.TestCase):
            
    def test_create_empty(self):
        #print("running test 1")
        d1 = MultiDict()
        d2 = MultiDict(None)

    def test_create_from_list(self):
        #print("running test 2")
        goodlist = [ (i, [i]) for i in range(5) ]
        badlist1 = [ (i, i) for i in range(5) ]
        badlist2 = [ i for i in range(5) ]
        
        d1 = MultiDict(goodlist)
        self.assertTrue(3 in d1[3])
        self.assertRaises(TypeError, lambda: MultiDict(badlist1))
        self.assertRaises(TypeError, lambda: MultiDict(badlist2))

    def test_create_from_dict(self):
        #print("running test 3")
        gooddict = { i: [i] for i in range(5) }
        baddict1 = { i: i for i in range(5) }
        gooddict2 = {'foaf:name': 'NERSC', 'foaf:page': 'http://www.nersc.gov/'}
        
        d1 = MultiDict(gooddict)
        self.assertTrue(3 in d1[3])
        self.assertRaises(TypeError, lambda: MultiDict(baddict1))
        d1 = MultiDict(gooddict2)
        self.assertEqual(d1['foaf:name'], 'NERSC')

    def test_create_from_kwargs(self):
        #print("running test 4")
        d1 = MultiDict(this=(1,), that=set([2]), the_other=[3])
        self.assertTrue(3 in d1['the_other'])
        self.assertRaises(TypeError, MultiDict, this=1, that=2, the_other=3)
        self.assertEqual(d1['this'].pop(), 1)

    def test_create_from_multidict(self):
        #print("running test 5")
        d1 = MultiDict(this=(1,), that=set([2]), the_other=[3])
        d2 = MultiDict(d1)
        self.assert_looks_equal(d1,d2)
        #d2.add('yet_another', [1,2,3])
        d2.add('yet_another', 1)
        self.assert_looks_different(d1, d2)

    def test_immutable(self):
        """ make sure that messing with a vale (set) gotten from the dict doesn't
            mess with what is stored in the dict
        """
        #print("running test 6")
        d1 = MultiDict(this=(1,), that=set([2]), the_other=[3])
        d2 = MultiDict(d1)
        that = d2['that']
        that.add(14)
        self.assert_looks_equal(d1,d2)

    def test_add(self):
        #print("running test 7")
        d1 = MultiDict(this=(1,), that=set([2]), the_other=[3])
        d2 = MultiDict(d1)
        d1.add('that', 'some string')
        self.assert_looks_different(d1, d2)

    def test_add_values(self):
        #print("running test 8")
        d1 = MultiDict(this=(1,), that=set([2]), the_other=[3])
        d2 = MultiDict(d1)
        d1.add_values('that', ['some string', 'another string'])
        self.assert_looks_different(d1, d2)
        # this actually works, because the letters in 'some string' form a set. It's probably
        # not what the user wanted, so raise a warning that the user can catch
        self.assertRaises(StringAsValuesWarning, d1.add_values, 'that', 'some string')
        self.assertRaises(TypeError, d1.add_values, 'that', 1)

    def test_remove(self):
        #print("running test 9")
        d1 = MultiDict(this=(1,), that=set([2]), the_other=[3])
        d2 = MultiDict(d1)
        d1.add_values('that', ['some string', 'another string'])
        d1.remove('that', 'some string')
        d1.remove('that', 'another string')
        self.assert_looks_equal(d1,d2)
        d1.add_values('that', ['some string', 'another string'])
        d1.remove('that', 'some string', 'another string')
        self.assert_looks_equal(d1,d2)


    # some utility functions for comparing dicts:
    def assert_looks_equal(self, d1, d2):
        for i in d1:
            self.assertTrue(d1[i]==d2[i])
        for i in d2:
            self.assertTrue(d1[i]==d2[i])

    def assert_looks_different(self, d1, d2):
        equal = True
        for i in d1:
            equal = equal and (d1[i]==d2[i] if i in d2 else False)
        for i in d2:
            equal = equal and (d1[i]==d2[i] if i in d1 else False)
        self.assertFalse(equal)


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.level = logging.DEBUG
    unittest.main()
 


