# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT


__all__ = [
    'commands_ip_route',
    'commands_iptables_forwarding',
    'is_ipv6',
]

CMD_IP = '/sbin/ip'
CMD_IPTABLESv4 = '/sbin/iptables'
CMD_IPTABLESv6 = '/sbin/ip6tables'

def is_ipv6(ip_addr):
    return (':' in ip_addr)

def commands_ip_route(device_name, ip, *, start=None, stop=None):
    assert bool(start) ^ bool(stop)
    cmd_ip = (CMD_IP, '-6') if is_ipv6(ip) else (CMD_IP, '-4')
    ip_verb = 'add' if start else 'del'
    commands = [
        (*cmd_ip, 'route', ip_verb, ip, 'dev', device_name),
    ]
    return commands

def commands_iptables_forwarding(device_name, ip, *, start=None, stop=None):
    assert bool(start) ^ bool(stop)
    iptables_cmd = '--insert' if start else '--delete'

    commands = []
    iptables = CMD_IPTABLESv6 if is_ipv6(ip) else CMD_IPTABLESv4
    commands.extend((
        (iptables, iptables_cmd, 'FORWARD', '--in-interface', device_name, '--source', ip, '-j', 'ACCEPT'),
        (iptables, iptables_cmd, 'FORWARD', '--out-interface', device_name, '--destination', ip, '-j', 'ACCEPT'),
    ))
    return commands

