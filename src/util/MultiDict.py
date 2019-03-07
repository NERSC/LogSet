#!/usr/bin/env python3

import sys
if sys.version_info < (3,5):
    raise Exception("Requires python 3.5+")

import logging
from typing import Set, Any, Iterable, Dict, Mapping, Hashable

class StringAsValuesWarning(Exception):
    def __init__(self,message=""):
        if not message:
            message = "passing a string in place of a list of values will add"
            message += " each char as a separate value"
        self.message = message

def make_set(iterable: Iterable[Any]) -> Set[Any]:
    if isinstance(iterable, str):
        raise TypeError(f"{type(iterable)} is not a non-string iterable")
    return set(iterable)

#import collections
#from collections.abc import Mapping
import six
class MultiDict(Mapping):
    """ A MultiDict is a dictionary where each key maps to a set of values.
        Rather than setting an item like mydict['a'] = 12, you need to add it 
        like mydict.add('a', 12). 
        A MultiDict can be created from another Mapping. If the source is a
        MultiDict, a shallow-ish copy will be made, otherwise the values in
        the mapping are taken to be the first item for each key
    """
    _storage: Dict[str,Any]
    def __init__(self, _source: Mapping = {}):
        if isinstance(_source, MultiDict):
            # semi-deep copy: copy each set in _storage
            self._storage = { 
                key: set(values) for key,values in _source._storage.items() 
            }
        else:
            self._storage = {}
            for key, value in _source.items():
                self.add(key, value)

    def __getitem__(self, key) -> Set[Any]:
        """ returns a copy of the stored set, not the set itself """
        return set(self._storage[key])

    def get(self, key: Hashable, default: Set[Any]=set()) -> Set[Any]:
        try:
            return set(self._storage[key])
        except KeyError:
            return default

    def __iter__(self):
        # iterates through keys, so no change from basic dict
        return iter(self._storage) 

    def __len__(self) -> int:
        """ the number of keys (each can have multiple values) """
        return len(self._storage)

    def __str__(self) -> str:
        return str(self._storage)

    #def one(self, key, default=None):
    def one(self, key) -> Any:
        """ return one (arbitrarily selected) value from key. This is useful 
            for entries that expect to only have one value
        """
        values = self._storage[key]
        return next(iter(values))

#        one = default
#        values = self._storage.get(key, None)
#        if values is None:
#            if default is None:
#                raise KeyError(key)
#        #    else:
#        #        return default
#        elif len(values)==0:
#            one = None
#        else:
#        #elif len(values)>0:
#            one = next(iter(values))
#        return one
#
#        #if values is not None and len(values)>0:
#        #    one = next(iter(values))

    def add(self, key, *values):
        if not values:
            raise TypeError("MultiDict.add requires at least one value")
        if key not in self._storage:
            self._storage[key] = set()
        for v in values:
            self._storage[key].add(v)

#    def add_values(self, key, values):
#        """ add contents of an iterable """
#        if not values:
#            raise TypeError("MultiDict.add_values requires at least one value")
#        if isinstance(values, six.string_types):
#            raise StringAsValuesWarning()
#        if key not in self._storage:
#            self._storage[key] = set()
#        self._storage[key] |= set(values)

    def remove(self, key, *args):
        self._storage[key] -= set(args)
        if not self._storage[key]:
            del self._storage[key]


import unittest
class TestMultiDict(unittest.TestCase):
            
    def test_create_empty(self):
        d1 = MultiDict()
        self.assertEqual(len(d1), 0)
        self.assertFalse(d1)

#    def test_create_from_sequence(self):
#        """ MultiDict should enforce that when creating from a sequence,
#            each element of the sequence is an iterable with 2 elements, 
#            the second itself being an iterable - but not a string (building
#            for most-common-usage, in which the client considers a string 
#            to be a basic type, rather than a container of letters
#        """
#        goodlist1 = [ (i, [i]) for i in range(5) ]
#        d1 = MultiDict(goodlist1)
#        self.assertTrue(3 in d1)
#        self.assertTrue(3 in d1[3])
#        self.assertEqual(len(d1), 5)
#        goodlist2 = [ (i, [1,2,3]) for i in range(5) ]
#        d2 = MultiDict(goodlist2)
#        self.assertTrue(3 in d2[3])
#        self.assertFalse(4 in d2[3])
#        self.assertEqual(len(d2), 5)
#
#        # a list of non-pairs should raise an error
#        badlist1 = [ i for i in range(5) ]
#        badlist2 = [ (i, i, i) for i in range(5) ]
#        badlist3 = [ (1,1), (1,2,3) ]
#        self.assertRaises(TypeError, lambda: MultiDict(badlist1))
#        self.assertRaises(TypeError, lambda: MultiDict(badlist2))
#        self.assertRaises(TypeError, lambda: MultiDict(badlist3))
#
#        # if the second item in a pair is a non-iterable or string,
#        # we should get an error
#        badlist4 = [ (i, i) for i in range(5) ]
#        badlist5 = [ (i, "hi there") for i in range(5) ]
#        badlist6 = [ (1, (1,2,3)), (2, 3) ]
#        self.assertRaises(TypeError, lambda: MultiDict(badlist4))
#        self.assertRaises(TypeError, lambda: MultiDict(badlist5))
#        self.assertRaises(TypeError, lambda: MultiDict(badlist6))

    def test_create_from_dict(self):
        dict1 = { i: i for i in range(5) }
        d1 = MultiDict(dict1)
        self.assertTrue(3 in d1[3])
        self.assertEqual(len(d1), 5)

        d2 = MultiDict(d1)
        self.assertTrue(3 in d2[3])
        self.assertEqual(len(d2), 5)

        d3 = MultiDict({'foaf:name': 'NERSC', 
                        'foaf:page': 'http://www.nersc.gov/'
        }) 
        self.assertEqual(len(d3), 2)
        self.assertEqual(len(d3['foaf:name']), 1)
        self.assertEqual(d3.one('foaf:name'), 'NERSC')

#        # dicts whose values are all (non-string) iterable should succeed
#        gooddict1 = { i: [i] for i in range(5) }
#        d1 = MultiDict(gooddict1)
#        self.assertTrue(3 in d1[3])
#        self.assertEqual(len(d1), 5)
#
#        gooddict2 = { i: (1,2,3) for i in range(5) }
#        d2 = MultiDict(gooddict2)
#        self.assertTrue(3 in d2[3])
#        self.assertEqual(len(d2), 5)
#
#        gooddict3 = {'foaf:name': ['NERSC'], 
#                     'foaf:page': ['http://www.nersc.gov/']
#        }
#        d3 = MultiDict(gooddict3)
#        self.assertEqual(len(d3), 2)
#        self.assertEqual(len(d3['foaf:name']), 1)
#        self.assertEqual(d3.one('foaf:name'), 'NERSC')
#
#        baddict1 = { i: i for i in range(5) }
#        self.assertRaises(TypeError, lambda: MultiDict(baddict1))
#
#        baddict2 = {'foaf:name': 'NERSC', 'foaf:page': 'http://www.nersc.gov/'}
#        self.assertRaises(TypeError, lambda: MultiDict(baddict2))

    def test_get_one(self):
        #d = MultiDict({'foaf:name': ['NERSC'], 'foaf:page': []})
        d = MultiDict({'foaf:name': 'NERSC'})
        self.assertEqual(d.one('foaf:name'), 'NERSC')
        self.assertRaises(KeyError, d.one, 'not a key')
        #self.assertIsNone(d.one('foaf:page'))

#    def test_create_from_kwargs(self):
#        d1 = MultiDict(this=(1,), that=set([2]), the_other=[3], a_string=["hi"])
#        self.assertTrue(3 in d1['the_other'])
#        self.assertEqual(d1['this'].pop(), 1)
#        self.assertEqual(d1['a_string'].pop(), "hi")
#        self.assertRaises(TypeError, MultiDict, this=1, that=2, the_other=3)
#        self.assertRaises(TypeError, MultiDict, this="hi", that="there")

    def test_create_from_multidict(self):
        d1 = MultiDict({ i: i for i in range(5) })
        d2 = MultiDict(d1)
        self.assert_looks_equal(d1,d2)
        d2.add('yet_another', 1)
        self.assert_looks_different(d1, d2)

    def test_immutable(self):
        """ make sure that messing with a value (set) gotten from the dict doesn't
            mess with what is stored in the dict
        """
        d1 = MultiDict({'this':1, 'that':2})
        d2 = MultiDict(d1)
        that = d2['that']
        that.add(14)
        self.assert_looks_equal(d1,d2)
        self.assertEqual(len(d1['that']), 1)
        self.assertEqual(len(d2['that']), 1)

    def test_add(self):
        d1 = MultiDict({'this':1, 'that':2})
        d2 = MultiDict(d1)
        d1.add('that', 'some string')
        self.assert_looks_different(d1, d2)

#    def test_add_values(self):
#        d1 = MultiDict(this=(1,), that=set([2]), the_other=[3])
#        d2 = MultiDict(d1)
#        d1.add_values('that', ['some string', 'another string'])
#        self.assert_looks_different(d1, d2)
#        # this actually works, because the letters in 'some string' form a set. It's probably
#        # not what the user wanted, so raise a warning that the user can catch
#        self.assertRaises(StringAsValuesWarning, d1.add_values, 'that', 'some string')
#        self.assertRaises(TypeError, d1.add_values, 'that', 1)

    def test_remove(self):
        d1 = MultiDict({'this':1, 'that':2})
        d2 = MultiDict(d1)
        d1.add('that', 'some string', 'another string')
        d3 = MultiDict(d1)
        d1.remove('that', 'some string')
        self.assert_looks_different(d1, d3)
        d1.remove('that', 'another string')
        self.assert_looks_equal(d1,d2)
        d1.add('that', 'some string', 'another string')
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
 


