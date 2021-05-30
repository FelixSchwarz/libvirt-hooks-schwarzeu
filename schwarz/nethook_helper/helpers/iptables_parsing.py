# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from collections import namedtuple
import re
import subprocess

from .routing import is_ipv6, CMD_IPTABLESv4, CMD_IPTABLESv6
from ..lib import AttrDict


__all__ = [
    'is_ip_present_in_iptables_config',
    'parse_iptables_output',
    'retrieve_iptables_config',
]

_IptablesData = namedtuple('_IptablesData', ('rules',))

def retrieve_iptables_config(chain, *, ipv6=False):
    cmd = [
        (CMD_IPTABLESv6 if ipv6 else CMD_IPTABLESv4),
        '-L', chain,
        '-vn'
    ]
    iptables_proc = subprocess.run(cmd, shell=False, stdout=subprocess.PIPE)
    return iptables_proc.stdout

def parse_iptables_output(output_str):
    rules = []
    header_fields = None
    for line_idx, line_str in enumerate(output_str.strip().split(b'\n')):
        if line_idx == 0:
            # Chain FORWARD (policy ACCEPT 0 packets, 0 bytes)
            continue
        fields = re.split('\s+', line_str.strip().decode('UTF-8'), maxsplit=9)
        if line_idx == 1:
            header_fields = fields + ['options']
            continue
        rule = AttrDict(zip(header_fields, fields))
        rules.append(rule)
    return _IptablesData(rules=rules)

def is_ip_present_in_iptables_config(ip, net_name, iptables_rules, *, log):
    _ipv6 = is_ipv6(ip)
    for rule in iptables_rules:
        if _is_reject_all(rule, net_name, ipv6=_ipv6):
            return False
        if rule.target == 'ACCEPT':
            if (rule['in'] == net_name) and (rule.source == ip):
                log.debug('ip already accepted: %r' % rule)
                return True
            elif (rule.out == net_name) and (rule.destination == ip):
                return True
    return False

def _is_reject_all(rule, net_name, *, ipv6):
    net_everything = '::/0' if ipv6 else '0.0.0.0/0'

    if rule.target != 'REJECT':
        return False
    elif (rule['in'] == net_name) and (rule.source == net_everything):
        return True
    elif (rule.out == net_name) and (rule.destination == net_everything):
        return True
    return False

