# libvirt-nethook-helper

This repo contains a [libvirt](https://libvirt.org/) `network` hook to route configured IP addresses to a certain libvirt network.

[Hetzner](https://www.hetzner.de) offers dedicated servers which can also run virtualized machines. However additional IP addresses need to be routed due to network security concerns (MAC address filtering). libvirt provides a `routed` networks but its builtin iptables rules block traffic from the outside to the bridge. This script adds `iptables` rules and sets up routing so traffic for specific IP addresses is forwarded from the external (Hetzner) network to the libvirt bridge.

## Installation

Tested on CentOS 7 and CentOS 8, Debian/Ubuntu may use different paths (pull requests welcome).

- clone this repo
- `$ ./setup.py bdist_wheel`
- copy `libvirt_nethook_helper-*.whl` to the libvirt machine.
- `# pip3 install libvirt_nethook_helper-*.whl` (bonus idea: use a virtual env in `/usr/local/`)
- create directory `/etc/libvirt/hooks/` if it does not exist
- create a symlink `/etc/libvirt/hooks/network` pointing to `/path/to/lv-setup-routed-ips`

Alternatively there is also a `.spec` file which you can use to create a RPM. That way you don't have to set up a virtualenv or use `pip`.


## Configuration

Routed IPs are configured in `/etc/sysconfig/routed-ips`.

Example

    # IP address         libvirt network name
    1.2.3.4              public


## Background / Behind the Scenes

To configure a VM with a routed IP with libvirt you need to do two things:

- Tell the Linux kernel which network device (libvirt bridge) should receive packets for the routed ip (`ip route add <IP> dev br-…`).
- Inject two IPtables rules into the `FORWARDING` chain to allow packages:
    - *to* the routed IP (via the libvirt bridge)
    - *from* the routed IP (originating from the libvirt bridge)

The main problem is that libvirtd automatically creates its own set of iptables rules which prevent any internet <-> libvirt bridge communication using the routed IPs. Another (though smaller) issue is that you can only set up the route when libvirt created the bridge but that comes *after* the main host networking configuration.

My code tackles both issues by listening to libvirt's `network` hook (`started`/`port-created`/`plugged`/`stopped`). Additionally it also works around a libvirt issue on CentOS 7 where a libvirtd restart (e.g. due to an RPM update) will wipe out the custom iptables configuration leaving your VMs inaccessible.

## Limitations / Caveats

Initially I created the repo to get some old ad-hoc code in a more deployable fashion. I envisioned unit tests and some easy-to-use hook files. However I did not get to that point as my timebox is running out. The current state should work though and at least the code is split up in multiple files, supports syslog logging and uses Python 3 now. Also paths to executables and configuration files are hard-coded right now. It works for me but of course making these configurable would be nice...

Using any `network` hook in libvirt will mark the network as "tainted":

    warning : networkNetworkObjTaint:5422 : Network name='...' uuid=... is tainted: hook-script

This warning is generally harmless and does not have any functional effects. The idea is somewhat similar to the taint flag in the Linux kernel ([initial libvirt patch](https://listman.redhat.com/archives/libvir-list/2014-February/msg00695.html), [blog post](https://www.berrange.com/posts/2011/12/19/using-command-line-arg-monitor-command-passthrough-with-libvirt-and-kvm/)): hooks are treated as some kind of internal API and buggy hooks can prevent libvirt from working. libvirt's tainting concept means that supporters can see pretty quickly if something "uncommon" was used. However [the hook API is publicly documented](https://libvirt.org/hooks.html) and is working fine for us since 2016.

Please note that there are no stability guarantees: Neither the current command name (`lv-setup-routed-ips`) nor the configuration syntax in (`/etc/sysconfig/routed-ips`) should be considered as "stable". I'll try not to break compatibility though. It would helpful to know if there are any external users though (so maybe just "star" this repo?) before spending any time to maintain compatibility.

## Other Projects / Additional Ressources

* libvirt [hooks documentation](https://libvirt.org/hooks.html)
* saschpe's [libvirt-hook-qemu](https://github.com/saschpe/libvirt-hook-qemu)
* doccaz' [kvm-scripts](https://github.com/doccaz/kvm-scripts)


