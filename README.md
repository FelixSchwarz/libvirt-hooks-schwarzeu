# libvirt-nethook-helper

This repo contains a [libvirt](https://libvirt.org/) `network` hook to route configured IP addresses to a certain libvirt network.

[Hetzner](https://www.hetzner.de) offers dedicated servers which can also run virtualized machines. However additional IP addresses need to be routed due to network security concerns (MAC address filtering). libvirt provides a `routed` networks but its builtin iptables rules block traffic from the outside to the bridge. This script adds `iptables` rules and sets up routing so traffic for specific IP addresses is forwarded from the external (Hetzner) network to the libvirt bridge.

## Installation

Tested on RHEL 8, Debian/Ubuntu may use different paths (pull requests welcome).

- clone this repo
- `$ ./setup.py bdist_wheel`
- copy `libvirt_nethook_helper-*.whl` to the libvirt machine.
- `# pip3 install libvirt_nethook_helper-*.whl` (bonus idea: use a virtual env in `/usr/local/`)
- create directory `/etc/libvirt/hooks/` if it does not exist
- create a symlink `/etc/libvirt/hooks/network` pointing to `/path/to/lv-setup-routed-ips`


## Configuration

Routed IPs are configured in `/etc/sysconfig/routed-ips`.

Example

    # IP address         libvirt network name
    1.2.3.4              public


## Limitations / Caveats

Initially I created the repo to get some old ad-hoc code in a more deployable fashion. I envisioned unit tests and some easy-to-use hook files. However I did not get to that point as my timebox is running out. The current state should work though and at least the code is split up in multiple files, supports syslog logging and uses Python 3 now.

Please note that there are no stability guarantees: Neither the current command name (`lv-setup-routed-ips`) nor the configuration syntax in (`/etc/sysconfig/routed-ips`) should be considered as "stable". I'll try not to break compatibility though. It would helpful to know if there are any external users though (so maybe just "star" this repo?) before spending any time to maintain compatibility.


## Other Projects / Additional Ressources

* libvirt [hooks documentation](https://libvirt.org/hooks.html)
* saschpe's [libvirt-hook-qemu](https://github.com/saschpe/libvirt-hook-qemu)
* doccaz' [kvm-scripts](https://github.com/doccaz/kvm-scripts)


