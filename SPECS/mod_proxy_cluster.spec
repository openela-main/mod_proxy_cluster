#no jars in this native build, so skip signing
%define _jarsign_opts --nocopy

# Update commitid and serial when new sources and release info is available
%global commitid eb56c23d62fe5dec0b4e3ecfcdb7a44f79abec5d
%global serial 1

Name:       mod_proxy_cluster
Summary: 	JBoss mod_proxy_cluster for Apache httpd
Version: 	1.3.18
Release: 	%{serial}%{?dist}
Epoch:		0
License: 	LGPLv3
Group: 		Applications/System
URL:		https://github.com/modcluster/mod_cluster
# You can get the tarball from https://github.com/modcluster/mod_cluster/archive/eb56c23d62fe5dec0b4e3ecfcdb7a44f79abec5d.tar.gz
Source0:        mod_cluster-%{commitid}.tar.gz
Source1:        %{name}.conf.sample
Source2:        %{name}.te
Source3:        %{name}.fc

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

# 64 bit natives only on RHEL 9
ExcludeArch:    i686 i386

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
* Fri Jan 20 2023 Sokratis Zappis <szappis@redhat.com> - 1.3.18-1
- Rebase mod_cluster to upstream 1.3.18.Final tag
- Related: rhbz#2158845

* Fri Aug 26 2021 George Zaronikas <gzaronik@redhat.com> - 1.3.14-23
- Adding policycoreutils-python-utils
- Related: rhbz#1964892

* Wed Aug 18 2021 George Zaronikas <gzaronik@redhat.com> - 1.3.14-22
- Fixing selinux policy
- Related: rhbz#1964892

* Wed Aug 18 2021 George Zaronikas <gzaronik@redhat.com> - 1.3.14-21
- Correcting conf name in gating tests.
- Related: rhbz#1964892

* Mon Aug 16 2021 Coty Sutherland <csutherl@redhat.com> - 1.3.14-20
- Cleanup spec file

* Mon Aug 09 2021 Mohan Boddu <mboddu@redhat.com> - 0:1.3.14-19.Final_redhat_2.1
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Mon Aug 02 2021 Coty Sutherland <csutherl@redhat.com> - 1.3.14-19.Final
- Fix broken test

* Mon Aug 02 2021 Coty Sutherland <csutherl@redhat.com> - 1.3.14-18.Final
- Fix typo in tests.yml filename

* Fri Jul 30 2021 George Zaronikas <gzaronik@redhat.com> - 1.3.14-17.Final
- Resolves: #1964892
