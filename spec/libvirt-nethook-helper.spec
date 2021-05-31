
%global dist_name libvirt_nethook_helper

%global py3_prefix python%{python3_pkgversion}

Name:           libvirt-nethook-helper
Version:        0.6
Release:        1%{?dist}
Summary:        Script to set up routed libvirt networks
License:        MIT
URL:            https://github.com/FelixSchwarz/libvirt-nethook-helper
Source0:        %{name}-%{version}.tar.gz
Source1:        %{name}-%{version}.tar.gz.asc
Source2:        0x77E0DB66.pub

Source10:       sysconfig-routed-ips
BuildArch:      noarch

# Used to verify OpenPGP signature
BuildRequires:  gnupg2
BuildRequires:  python3-devel
BuildRequires:  %{py3_prefix}-nose
# /sbin/ip
Requires:       iproute
# /sbin/iptables, /sbin/ip6tables
Requires:       iptables


%description
A libvirt network hook to route configured IP addresses to a specific libvirt
network. This makes "routed" libvirt networks usable as the default iptables
rules are too strict.

%prep
# remove this line if you are building a custom RPM (or add your public key
# for SOURCE2)
%{gpgverify} --keyring='%{SOURCE2}' --signature='%{SOURCE1}' --data='%{SOURCE0}'
%autosetup -p1 -n %{name}-%{version}

%build
%py3_build


%install
%py3_install
rm -rf %{buildroot}%{python3_sitelib}/tests
mkdir --parents %{buildroot}%{_libexecdir}/
mv %{buildroot}%{_bindir}/lv-setup-routed-ips %{buildroot}%{_libexecdir}/
mkdir --parents %{buildroot}%{_sysconfdir}/sysconfig
install --preserve-timestamps \
    %{SOURCE10} %{buildroot}%{_sysconfdir}/sysconfig/routed-ips


%check
nosetests-%{python3_version}

%files
%license LICENSE.txt
%doc README.md
%{_libexecdir}/lv-setup-routed-ips
%config(noreplace) %{_sysconfdir}/sysconfig/routed-ips
%dir %{python3_sitelib}/schwarz
%{python3_sitelib}/schwarz/nethook_helper
%{python3_sitelib}/%{dist_name}-%{version}-py*.egg-info/
%{python3_sitelib}/%{dist_name}-%{version}-py*-nspkg.pth


%changelog
* Mon May 31 2021 Felix Schwarz <felix.schwarz@oss.schwarz.eu> 0.6-1
- update to 0.6

* Thu May 27 2021 Felix Schwarz <felix.schwarz@oss.schwarz.eu> 0.5-2
- move helper script to /usr/libexec

* Wed May 26 2021 Felix Schwarz <felix.schwarz@oss.schwarz.eu> 0.5-1
- initial package

