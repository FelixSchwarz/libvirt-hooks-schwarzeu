# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT


__all__ = ['get_routing_commands']

CMD_IP = '/sbin/ip'
CMD_IPTABLESv4 = '/sbin/iptables'
CMD_IPTABLESv6 = '/sbin/ip6tables'

def get_routing_commands(action, device_name, routed_ips):
    assert (action in ('started', 'stopped'))
    if action == 'started':
        ip_verb = 'add'
        iptables_cmd = '--insert'
    else:
        ip_verb = 'del'
        iptables_cmd = '--delete'

    commands = []
    is_ipv6 = lambda ip_addr: (':' in ip_addr)
    for ip in routed_ips:
        if is_ipv6(ip):
            iptables = CMD_IPTABLESv6
            cmd_ip = (CMD_IP, '-6')
        else:
            iptables = CMD_IPTABLESv4
            cmd_ip = (CMD_IP, '-4')

        commands.extend((
            (iptables, iptables_cmd, 'FORWARD', '--in-interface', device_name, '--source', ip, '-j', 'ACCEPT'),
            (iptables, iptables_cmd, 'FORWARD', '--out-interface', device_name, '--destination', ip, '-j', 'ACCEPT'),
            (*cmd_ip, 'route', ip_verb, ip, 'dev', device_name),
        ))
    return commands

