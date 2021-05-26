
%global dist_name libvirt_nethook_helper

Name:           libvirt-nethook-helper
Version:        0.5
Release:        1%{?dist}
Summary:        Script to set up routed libvirt networks
License:        MIT
URL:            https://github.com/FelixSchwarz/libvirt-nethook-helper
Source0:        %{name}-%{version}.tar.gz
Source1:        sysconfig-routed-ips
BuildArch:      noarch

BuildRequires:  python3-devel
# /sbin/ip
Requires:       iproute
# /sbin/iptables, /sbin/ip6tables
Requires:       iptables


%description
A libvirt network hook to route configured IP addresses to a specific libvirt
network. This makes "routed" libvirt networks usable as the default iptables
rules are too strict.

%prep
%autosetup -p1 -n %{name}-%{version}

%build
%py3_build


%install
%py3_install
mkdir --parents %{buildroot}%{_sysconfdir}/sysconfig
install --preserve-timestamps \
    %{SOURCE1} %{buildroot}%{_sysconfdir}/sysconfig/routed-ips


%files
%license LICENSE.txt
%doc README.md
%{_bindir}/lv-setup-routed-ips
%config(noreplace) %{_sysconfdir}/sysconfig/routed-ips
%dir %{python3_sitelib}/schwarz
%{python3_sitelib}/schwarz/nethook_helper
%{python3_sitelib}/%{dist_name}-%{version}-py*.egg-info/
%{python3_sitelib}/%{dist_name}-%{version}-py*-nspkg.pth


%changelog
* Wed May 26 2021 Felix Schwarz <felix.schwarz@oss.schwarz.eu> 0.5-1
- initial package

