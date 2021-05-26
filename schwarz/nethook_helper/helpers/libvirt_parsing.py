# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from collections import namedtuple
from xml.etree import ElementTree


__all__ = ['parse_libvirt_net_data']

_LibvirtNetData = namedtuple('_LibvirtNetData', ('device_name', 'device_ipv4'))

def parse_libvirt_net_data(network_xml):
    root = ElementTree.fromstring(network_xml)
    device_name = root.find('network/bridge').get('name')
    device_ipv4 = root.find('network/ip').get('address')
    return _LibvirtNetData(
        device_name = device_name,
        device_ipv4 = device_ipv4,
    )

