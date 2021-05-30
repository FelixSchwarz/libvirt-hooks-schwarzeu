# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

from collections import namedtuple
import logging
from logging.handlers import SysLogHandler
from pathlib import Path
import re
import shlex
import subprocess
import sys

from .helpers import *


__all__ = []

ROUTING_FILE = '/etc/sysconfig/routed-ips'
LOG_LEVEL = logging.DEBUG
SYSLOG_IDENT = 'libvirt-nethook-helper'

handled_events = {
    'network': [
        # "start" or "started" would be a good choice to set up routing but
        # for CentOS 7 libvirtd will inject its iptables configuration whenever
        # libvirtd is restarted. That means VMs with routed IPs are not
        # accessible anymore after "service restart libvirtd" (or an automatic
        # update of libvirtd, which triggers a daemon restart as well).
        #
        # Therefore we listed to the "plugged" event which is triggered
        # whenever a new VM is started. Conveniently this event is also
        # triggered after a daemon restart if a VM is already running.
        # "started" is only used to configure "ip route"
        ('started', 'begin'),
        ('plugged', 'begin'),

        # We can not undo our changed in "unpluged" event because our
        # configuration currently does not contain a reference to specific VMs.
        # The "unplugged" event is triggered whenever a (any) VM is shut down
        # but if there are multiple VMs we must not undo *all* of our
        # configuration when just one VM is down. We need to use the "stopped"
        # event instead.
        #('unplugged', 'begin'),
        # The "stopped" event is triggered when the libvirt network is being
        # shut down.
        ('stopped', 'end'),
    ],
}

def main_ip_routing(argv=sys.argv):
    log = setup_logging()
    try:
        return _main_ip_routing(argv, log=log)
    except:
        if not sys.stdout.isatty():
            log.exception('unhandled exception in "_main"')
        return 100

def _main_ip_routing(argv, *, log):
    event = check_for_handled_event(argv, log=log)
    if event.rc is not None:
        return event.rc
    return event.handler(event, log=log)


EventParams = namedtuple('EventParams', (
    'rc',
    'exe_name',
    'res_name',
    'action',
    'state',
    'libvirt_xml',
    'handler',
))
EventParams.__new__.__defaults__ = (None,) * len(EventParams._fields)

def check_for_handled_event(argv, *, log):
    if len(argv) < 5:
        sys.stderr.write(f'usage: {argv[0]} NETWORK_NAME ACTION STATUS -\n')
        if not sys.stdout.isatty():
            log.error(f'bad call to {argv[0]}: {shlex.join(argv)}')
        return EventParams(rc=1)
    (exe_name, res_name, action, state, libvirt_xml) = argv[:5]

    # on CentOS 7 argv[0] contains the absolute path to the executable
    exe_fn = Path(exe_name).name
    # helpful to debug triggered events
    # log.debug(f'{exe_fn} "{res_name}": action="{action}", state="{state}"')
    handled_combinations = handled_events.get(exe_fn, ())
    if action not in dict(handled_combinations):
        return EventParams(rc=0)

    log.debug(f'{exe_fn} "{res_name}": action="{action}", state="{state}"')
    if (action, state) not in handled_combinations:
        error_msg = f'unhandled combination: {action} {state}'
        sys.stderr.write(error_msg + '\n')
        log.error(error_msg)
        return EventParams(rc=2)

    if libvirt_xml == '-':
        libvirt_xml = sys.stdin.read()

    return EventParams(
        exe_name    = exe_fn,
        res_name    = res_name,
        action      = action,
        state       = state,
        libvirt_xml = libvirt_xml,
        handler     = handle_network_hook,
    )


def handle_network_hook(event, *, log):
    net_name = event.res_name
    action = event.action

    net_meta = parse_libvirt_net_data(event.libvirt_xml)
    if action == 'started':
        routes_added = setup_ip_routing(net_name, net_meta, log=log)
        if routes_added:
            log.info(f'IP routing for "{net_name}" (action="{action}") configured.')
    else:
        cfg_present = allow_ip_forwarding(net_name, net_meta, action, log=log)
        if cfg_present:
            log.info(f'IP forwarding for "{net_name}" (action="{action}") configured.')
        else:
            log.debug(f'no configuration for "{net_name}" (action="{action}")')
    return 0


def setup_logging():
    syslog_h = SysLogHandler(address='/dev/log')
    # Python's SysLogHandler just prepends the "ident" string before each log
    # message so we need an extra space after the actual identification.
    # .ident attribute present Python 3.3+ (https://bugs.python.org/issue12419)
    syslog_h.ident = SYSLOG_IDENT + ' '

    logger = logging.getLogger('nethook_helper')
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(syslog_h)
    return logger

def setup_ip_routing(net_name, net_meta, *, log):
    routing_cfg_path = Path(ROUTING_FILE)
    address_lines = read_lines_from_file(routing_cfg_path)
    routed_ips = addresses_for_network(address_lines, net_name)
    if not routed_ips:
        return
    log.debug(f'network "{net_name}": routed IPs={", ".join(routed_ips)}')

    log_prefix = f'network="{net_name}": '
    device = net_meta.device_name

    commands = []
    for ip in routed_ips:
        commands.extend(
            commands_ip_route(device, ip, start=True)
        )
        log.debug(f'routing {ip} to this network')
    if commands:
        _run_commands(commands, log=log, log_prefix=log_prefix)

    return bool(commands)

def allow_ip_forwarding(net_name, net_meta, action, *, log):
    routing_cfg_path = Path(ROUTING_FILE)
    address_lines = read_lines_from_file(routing_cfg_path)
    routed_ips = addresses_for_network(address_lines, net_name)
    if not routed_ips:
        return
    log.debug(f'network "{net_name}": routed IPs={", ".join(routed_ips)}')

    start = (action == 'plugged')
    stop = not start
    log_prefix = f'network="{net_name}"/action="{action}": '

    commands = []
    device = net_meta.device_name
    for ip in routed_ips:
        iptables_str = retrieve_iptables_config(chain='FORWARD', ipv6=is_ipv6(ip))
        iptables_data = parse_iptables_output(iptables_str)
        # LATER: The check is a bit simplistic.
        # Assumption: Any ACCEPT rule for the given IP indicates that IP
        # forwarding is set up correctly in iptables. However it is probably
        # more robust to check that the exact generated iptables rules are
        # actually present.
        is_configured = is_ip_present_in_iptables_config(ip, device, iptables_data.rules, log=log)
        if start and not is_configured:
            log.debug(log_prefix + f'IP {ip} not configured for forwarding')
            commands.extend(
                commands_iptables_forwarding(device, ip, start=True)
            )
        elif stop and is_configured:
            log.debug(log_prefix + f'remove forwarding rules for IP {ip}')
            commands.extend(
                commands_iptables_forwarding(device, ip, stop=True)
            )
    if commands:
        _run_commands(commands, log=log, log_prefix=log_prefix)

    return bool(commands)


def _run_commands(commands, *, log, log_prefix):
    for cmd in commands:
        cmd_str = ' '.join(cmd)
        try:
            subprocess.check_call(cmd, shell=False)
            result = True
        except:
            result = False
        log_msg = log_prefix + f'{cmd_str}'
        if not result:
            log.error(log_msg + ' -> ERROR')
        else:
            log.debug(log_msg)


def addresses_for_network(address_data, network_name):
    addresses = []
    for line in address_data:
        if line.strip() == '':
            continue
        elif re.search('^\s*#', line):
            continue
        match = re.search('^\s*(\S+)\s+(\w+)\s*$', line)
        if not match:
            continue
        ip_str = match.group(1)
        net_name = match.group(2)
        if net_name != network_name:
            continue
        addresses.append(ip_str)
    return addresses


def read_lines_from_file(cfg_path):
    if not cfg_path.exists():
        return
    with cfg_path.open('r') as fp:
        for line in fp.readlines():
            yield line

