# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT


from unittest import TestCase

from schwarz.nethook_helper.helpers import parse_iptables_output

assert_equals = None


class IptablesParsingTest(TestCase):
    def setUp(self):
        global assert_equals
        assert_equals = lambda first, second, message=None: self.assertEqual(first, second, msg=message)

    def test_can_parse_iptables_output(self):
        output_str = b'''
Chain FORWARD (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination
    0     0 ACCEPT     all  --  *      br-public  0.0.0.0/0            10.1.2.3
    0     0 ACCEPT     all  --  br-public *       10.1.2.3             0.0.0.0/0
    0     0 ACCEPT     all  --  br-public br-public  0.0.0.0/0            0.0.0.0/0
    1    68 REJECT     all  --  *      br-public  0.0.0.0/0            0.0.0.0/0            reject-with icmp-port-unreachable
        '''.strip()

        iptables_meta = parse_iptables_output(output_str)
        assert_equals(4, len(iptables_meta.rules))
        rule1, rule2, rule3, rule4 = iptables_meta.rules

        _r = _Rule
        assert_attrs_equal(rule1,
            **_r(target='ACCEPT', in_='*', out='br-public', source='0.0.0.0/0', destination='10.1.2.3'))
        assert_attrs_equal(rule2,
            **_r(target='ACCEPT', in_='br-public', out='*', source='10.1.2.3', destination='0.0.0.0/0'))
        assert_attrs_equal(rule3,
            **_r(target='ACCEPT', in_='br-public', out='br-public', source='0.0.0.0/0', destination='0.0.0.0/0'))
        assert_attrs_equal(rule4,
            **_r(target='REJECT', in_='*', out='br-public', source='0.0.0.0/0', destination='0.0.0.0/0'))


def _Rule(**kwargs):
    if 'in_' in kwargs:
        kwargs['in'] = kwargs.pop('in_')
    return kwargs

def assert_attrs_equal(obj, **attrs):
    for attr_name, expected_value in attrs.items():
        actual_value = getattr(obj, attr_name)
        assert_equals(expected_value, actual_value, message=attr_name)

