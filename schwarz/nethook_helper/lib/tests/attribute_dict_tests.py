# -*- coding: UTF-8 -*-

# License: Public Domain
# Authors: Felix Schwarz <felix.schwarz@oss.schwarz.eu>
#
# Version 1.2

from unittest import TestCase

from ..attribute_dict import *


class AttributDictTests(TestCase):
    def test_can_use_class_as_dict(self):
        obj = AttrDict(foo=1, bar=2)
        self.assertEquals(1, obj['foo'])
        self.assertEquals(2, obj['bar'])

    def test_can_access_items_as_attributes(self):
        obj = AttrDict(foo=1, bar=2)
        self.assertEquals(1, obj.foo)
        self.assertEquals(2, obj.bar)

    def test_can_set_values_via_attributes(self):
        obj = AttrDict(foo=1, bar=2)
        obj.foo = 21
        self.assertEquals(21, obj.foo)
        obj.bar = 42
        self.assertEquals(42, obj.bar)

    def test_raise_attribute_error_for_non_existent_keys(self):
        obj = AttrDict(foo=1)
        self.assertRaises(AttributeError, getattr, obj, 'invalid')
        self.assertRaises(AttributeError, setattr, obj, 'invalid', 'something')

    def test_can_copy_instances(self):
        obj = AttrDict(foo=1, bar=2)
        clone = obj.copy()
        self.assertEquals(obj, clone)

        clone.bar = 42
        self.assertNotEquals(obj, clone)
        self.assertEquals(2, obj.bar)

