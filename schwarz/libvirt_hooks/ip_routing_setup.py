# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

import logging
from logging.handlers import SysLogHandler
from pathlib import Path
import re
import shlex
import subprocess
import sys

from .helpers import get_routing_commands, parse_libvirt_net_data


__all__ = []

ROUTING_FILE = '/etc/sysconfig/routed-ips'
LOG_LEVEL = logging.DEBUG


def main_ip_routing(argv=sys.argv):
    log = setup_logging()
    try:
        return _main_ip_routing(argv, log=log)
    except:
        if not sys.stdout.isatty():
            log.exception('unhandled exception in "_main"')
        return 100

def _main_ip_routing(argv, *, log):
    if len(argv) < 5:
        sys.stderr.write(f'usage: {argv[0]} NETWORK_NAME ACTION STATUS -\n')
        if not sys.stdout.isatty():
            log.error(f'bad call to {argv[0]}: {shlex.join(argv)}')
        return 1

    net_name, action, state, network_xml = argv[1:5]
    if action not in ('started', 'stopped'):
        return 0
    handled_combinations = (
        ('started', 'begin'),
        ('stopped', 'end'),
    )
    if (action, state) not in handled_combinations:
        error_msg = f'unhandled combination: {action} {state}'
        sys.stderr.write(error_msg + '\n')
        log.error(error_msg)
        return 2

    if network_xml == '-':
        network_xml = sys.stdin.read()
    net_meta = parse_libvirt_net_data(network_xml)

    cfg_present = setup_ip_routing(net_name, net_meta, action, log=log)
    if cfg_present:
        log.info(f'IP routing for "{net_name}" (action="{action}") configured.')
    else:
        log.info(f'no configuration for "{net_name}" (action="{action}")')
    return 0


def setup_logging():
    syslog_h = SysLogHandler(address='/dev/log')
    # Python's SysLogHandler just prepends the "ident" string before each log
    # message so we need an extra space after the actual identification.
    # .ident attribute present Python 3.3+ (https://bugs.python.org/issue12419)
    syslog_h.ident = 'libvirt-hooks '

    logger = logging.getLogger('hook-logs')
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(syslog_h)
    return logger

def setup_ip_routing(net_name, net_meta, action, *, log):
    routing_cfg_path = Path(ROUTING_FILE)
    address_lines = read_lines_from_file(routing_cfg_path)
    routed_ips = addresses_for_network(address_lines, net_name)
    if not routed_ips:
        return
    log.debug(f'network "{net_name}": routed IPs={", ".join(routed_ips)}')
    commands = get_routing_commands(action, net_meta.device_name, routed_ips)
    for cmd in commands:
        cmd_str = ' '.join(cmd)
        try:
            subprocess.check_call(cmd, shell=False)
            result = True
        except:
            result = False
        log_msg = f'network="{net_name}"/action="{action}": {cmd_str}'
        if not result:
            log.error(log_msg + ' -> ERROR')
        else:
            log.debug(log_msg)
    return bool(commands)


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

