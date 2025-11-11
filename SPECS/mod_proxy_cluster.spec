#no jars in this native build, so skip signing
%define _jarsign_opts --nocopy

# Update commitid and serial when new sources and release info is available
%global commitid 42b64bbafb597df26b7c7441e922f295b238247c
%global serial 2

Name:         mod_proxy_cluster
Summary:      JBoss mod_proxy_cluster for Apache httpd
Version:      1.3.22
Release:      %{serial}%{?dist}
Epoch:        0
License:      LGPLv3
Group:        Applications/System
URL:          https://github.com/modcluster/mod_cluster
# You can get the tarball from https://github.com/modcluster/mod_cluster/archive/45265ef9c1f53c71af5241f9deae19fd839263c8.tar.gz
Source0:      mod_cluster-%{commitid}.tar.gz
Source1:      %{name}.conf.sample
Source2:      %{name}.te
Source3:      %{name}.fc

BuildRoot:    %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

# 64 bit natives only on RHEL 10
ExcludeArch:      i686 i386

BuildRequires:	  httpd-devel
BuildRequires:	  apr-devel
BuildRequires:	  apr-util-devel
BuildRequires:	  autoconf
BuildRequires:    gcc
BuildRequires:    selinux-policy-devel
Requires(post):   policycoreutils-python-utils, python3-policycoreutils
Requires(postun): policycoreutils-python-utils, python3-policycoreutils

Requires:   httpd >= 0:2.4.6
Requires:   apr
Requires:   apr-util

%description
JBoss mod_proxy_cluster for Apache httpd.

%prep
%setup -q -n mod_cluster-%{commitid}

%build
%{!?apxs: %{expand: %%define apxs %{_sbindir}/apxs}}
%define aplibdir %(%{apxs} -q LIBEXECDIR 2>/dev/null)

pushd native
for i in advertise mod_manager mod_proxy_cluster mod_cluster_slotmem
do
pushd $i
set -e
sh buildconf
./configure --with-apxs=/usr/bin/apxs
make CFLAGS="%{optflags} -fno-strict-aliasing -DMOD_CLUSTER_RELEASE_VERSION=\\\"-%{serial}\\\""
popd
done
popd

%install
%define aplibdir /usr/lib64/httpd/modules/
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}
install -d -m 755 $RPM_BUILD_ROOT/%{aplibdir}/
cp -p native/*/*.so ${RPM_BUILD_ROOT}/%{aplibdir}/
install -d -m 755 $RPM_BUILD_ROOT/%{_localstatedir}/cache/httpd/mod_proxy_cluster

install -d -m 755 $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d/
install -p -m 644 %{SOURCE1} \
        $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d/mod_proxy_cluster.conf.sample

# for SELinux
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/selinux/packages/%{name}
mkdir selinux
pushd selinux
    cp -p %{SOURCE2} .
    cp -p %{SOURCE3} .

    make -f %{_datadir}/selinux/devel/Makefile
    install -p -m 644 -D %{name}.pp $RPM_BUILD_ROOT%{_datadir}/selinux/packages/%{name}/mod_proxy_cluster.pp
popd

%clean
rm -Rf $RPM_BUILD_ROOT

%post
if [ $1 -eq 1 ] ; then
    %{_sbindir}/semodule -i %{_datadir}/selinux/packages/%{name}/mod_proxy_cluster.pp 2>/dev/null || :
    %{_sbindir}/semanage port -a -t http_port_t -p udp 23364 >/dev/null 2>&1 || :
    %{_sbindir}/semanage port -a -t http_port_t -p tcp 6666 >/dev/null 2>&1 || :
    /sbin/restorecon -R /var/cache/httpd/mod_proxy_cluster >/dev/null 2>&1 || :
fi

%preun
if [ $1 -eq 0 ] ; then
    %{_sbindir}/semanage port -d -t http_port_t -p udp 23364 2>&1 || :
    %{_sbindir}/semanage port -d -t http_port_t -p tcp 6666 2>&1 || :
    %{_sbindir}/semodule -r mod_proxy_cluster >/dev/null 2>&1 || :
    /sbin/restorecon -R /var/cache/httpd/mod_proxy_cluster >/dev/null 2>&1 || :
fi

%files
%{!?apxs: %{expand: %%define apxs /usr/bin/apxs}}
%define aplibdir /usr/lib64/httpd/modules/
%defattr(0644,root,root,0755)
%doc lgpl.txt
%dir %{_localstatedir}/cache/httpd/mod_proxy_cluster
%attr(0755,root,root) %{aplibdir}/*
%{_sysconfdir}/httpd/conf.d/mod_proxy_cluster.conf.sample
# for SELinux
%dir %{_datadir}/selinux/packages/%{name}
%{_datadir}/selinux/packages/%{name}/mod_proxy_cluster.pp


%changelog
* Wed Mar 05 2025 Sokratis Zappis <szappis@redhat.com> - 1.3.22-2.el10
- Resolves: RHEL-82256 - Update deprecated misspeled EnableMCPMReceive directive

* Mon Feb 24 2025 Vladimír Chlup <vchlup@redhat.com> - 1.3.22-1
- Resolves: RHEL-80480 Rebase mod_proxy_cluster to upstream 1.3.22.Final release

* Fri Jan 24 2025 Vladimír Chlup <vchlup@redhat.com> - 1.3.21-1
- Resolves: RHEL-76000 Rebase mod_proxy_cluster to upstream 1.3.21.Final release

* Tue Oct 29 2024 Troy Dawson <tdawson@redhat.com> - 0:1.3.20-1.1
- Bump release for October 2024 mass rebuild:
  Resolves: RHEL-64018

* Wed Aug 21 2024 Sokratis Zappis <szappis@redhat.com> - 1.3.20-1
- Rebase mod_proxy_cluster to upstream 1.3.20.Final tag
- Related: RHEL-55407 - Rebase mod_proxy_cluster to upstream 1.3.20.Final release

* Mon Jun 24 2024 Troy Dawson <tdawson@redhat.com> - 1.3.19-1.2
- Bump release for June 2024 mass rebuild

* Sun Jan 21 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.19-1.1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Wed Sep 20 2023 Hui Wang <huwang@redhat.com> - 1.3.19-1
- First build
