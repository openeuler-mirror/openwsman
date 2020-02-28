%bcond_with pam

# RubyGems's macros expect gem_name to exist.
%global		gem_name %{name}

Name:		openwsman
Version:	2.6.5
Release:	11
Summary:	Opensource Implementation of WS-Management
License:	BSD
URL:		http://www.openwsman.org/
Source0:	https://github.com/Openwsman/openwsman/archive/v%{version}.tar.gz
Source1:	openwsmand.8.gz
Source2:	openwsmand.service
Source3:	owsmantestcert.sh
%if %{with pam}
Patch1:		openwsman-2.4.0-pamsetup.patch
%endif
Patch2:		openwsman-2.4.12-ruby-binding-build.patch
Patch3:		openwsman-2.6.2-openssl-1.1-fix.patch
Patch4:		openwsman-2.6.5-fix-set-cipher-list-retval-check.patch
Patch5:		openwsman-2.6.5-libcurl-error-codes-update.patch
Patch6000:     CVE-2019-3833.patch

BuildRequires:	swig libcurl-devel libxml2-devel pam-devel sblim-sfcc-devel python3
BuildRequires:	python3-devel ruby ruby-devel rubygems-devel perl-interpreter
BuildRequires:	perl-devel perl-generators pkgconfig openssl-devel
BuildRequires:	cmake systemd-units gcc gcc-c++ python2 python2-devel


%description
Opensource Implementation of WS-Management protocol stack

%package -n libwsman1
License:	BSD
Summary:	Opensource Implementation of WS-Management
Provides:	%{name} = %{version}-%{release}
Obsoletes:	%{name} < %{version}-%{release}

%description -n libwsman1
Opensource Implementation of WS-Management protocol stack
(Common libraries)

%package -n libwsman-devel
License:	BSD
Summary:	Opensource Implementation of WS-Management
Provides:	%{name}-devel = %{version}-%{release}
Obsoletes:	%{name}-devel < %{version}-%{release}
Requires:	libwsman1 = %{version}-%{release}
Requires:	%{name}-server = %{version}-%{release}
Requires:	%{name}-client = %{version}-%{release}
Requires:	sblim-sfcc-devel libxml2-devel libcurl-devel

%if %{with pam}
Requires:	pam-devel
%endif
%description -n libwsman-devel
Opensource Implementation of WS-Management stack
(Development files)

%package client
License:	BSD
Summary:	Openwsman Client libraries

%description client
Openwsman Client libraries.

%package server
License:	BSD
Summary:	Openwsman Server and service libraries
Requires:	libwsman1 = %{version}-%{release}

%description server
Openwsman Server and service libraries.

%package python3
License:	BSD
Summary:	Python bindings for openwsman client API
Requires:	python3
Requires:	libwsman1 = %{version}-%{release}
%{?python_provide:%python_provide python3-openwsman}

%description python3
This package provides Python3 bindings to access the openwsman client API.

%if %{with pam}
%package ruby
License:	BSD
Summary:	Ruby bindings for openwsman client API
Obsoletes:	%{name}-ruby < %{version}-%{release}

%description -n rubygem-%{gem_name}
This package provides Ruby bindings to access the openwsman client API.

%package ruby-docs
Summary:	HTML documentation for Opendwsman Ruby bindings
BuildArch:	noarch

%description ruby-docs
This package provides HTML documentation for the Openwsman Ruby
bindings.

%endif

%package perl
License:	BSD
Requires:	perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))
Summary:	Perl bindings for openwsman client API
Requires:	libwsman1 = %{version}-%{release}

%description perl
This package provides Perl bindings to access the openwsman client API.

%package winrs
Summary:	Windows Remote Shell
Requires:	rubygem-%{gem_name} = %{version}-%{release}

%description winrs
This is a command line tool for the Windows Remote Shell protocol.
You can use it to send shell commands to a remote Windows hosts.

%package_help

%prep
%autosetup -p1

%build
# Removing executable permissions on .c and .h files to fix rpmlint warnings. 
chmod -x src/cpp/WsmanClient.h

mkdir build

export RPM_OPT_FLAGS="$RPM_OPT_FLAGS -DNO_SSL_CALLBACK"
export CFLAGS="-D_GNU_SOURCE -fPIE -DPIE"
export LDFLAGS="$LDFLAGS -Wl,-z,now -pie"
cd build
cmake \
	-DCMAKE_INSTALL_PREFIX=/usr \
	-DCMAKE_VERBOSE_MAKEFILE=TRUE \
	-DCMAKE_BUILD_TYPE=Release \
	-DCMAKE_C_FLAGS_RELEASE:STRING="$RPM_OPT_FLAGS -fno-strict-aliasing" \
	-DCMAKE_CXX_FLAGS_RELEASE:STRING="$RPM_OPT_FLAGS" \
	-DCMAKE_SKIP_RPATH=1 \
	-DPACKAGE_ARCHITECTURE=`uname -m` \
	-DLIB=%{_lib} \
	-DBUILD_JAVA=no \
%if %{without pam}
	-DBUILD_RUBY_GEM=no \
%endif
	..

make

%if %{with pam}
# Make the freshly build openwsman libraries available to build the gem's
# binary extension.
export LIBRARY_PATH=%{_builddir}/%{name}-%{version}/build/src/lib
export CPATH=%{_builddir}/%{name}-%{version}/include/
export LD_LIBRARY_PATH=%{_builddir}/%{name}-%{version}/build/src/lib/
%endif

%if %{with pam}
%gem_install -n ./bindings/ruby/%{name}-%{version}.gem
%endif

%install
cd build

%if %{with pam}
# Do not install the ruby extension, we are proviging the rubygem- instead.
echo -n > bindings/ruby/cmake_install.cmake
%endif

%make_install
cd ..
rm -f %{buildroot}/%{_libdir}/*.la
rm -f %{buildroot}/%{_libdir}/openwsman/plugins/*.la
rm -f %{buildroot}/%{_libdir}/openwsman/authenticators/*.la
[ -d %{buildroot}/%{ruby_vendorlibdir} ] && rm -f %{buildroot}/%{ruby_vendorlibdir}/openwsmanplugin.rb
[ -d %{buildroot}/%{ruby_vendorlibdir} ] && rm -f %{buildroot}/%{ruby_vendorlibdir}/openwsman.rb
install -d %{buildroot}%{_sysconfdir}/init.d
install -m 644 etc/openwsman.conf %{buildroot}/%{_sysconfdir}/openwsman
install -m 644 etc/openwsman_client.conf %{buildroot}/%{_sysconfdir}/openwsman
install -d %{buildroot}/%{_unitdir}
install -p -m 644 %{SOURCE2} %{buildroot}/%{_unitdir}/openwsmand.service
install -m 644 etc/ssleay.cnf %{buildroot}/%{_sysconfdir}/openwsman
install -p -m 755 %{SOURCE3} %{buildroot}/%{_sysconfdir}/openwsman
install -d %{buildroot}/%{_mandir}/man8/
cp %SOURCE1 %{buildroot}/%{_mandir}/man8/
install -m 644 include/wsman-xml.h %{buildroot}/%{_includedir}/openwsman
install -m 644 include/wsman-xml-binding.h %{buildroot}/%{_includedir}/openwsman
install -m 644 include/wsman-dispatcher.h %{buildroot}/%{_includedir}/openwsman

%if %{with pam}
install -d %{buildroot}%{gem_dir}
cp -pa ./build%{gem_dir}/* %{buildroot}%{gem_dir}/
install -d %{buildroot}%{gem_extdir_mri}
cp -a ./build%{gem_extdir_mri}/{gem.build_complete,*.so} %{buildroot}%{gem_extdir_mri}/
%endif

%post -n libwsman1 -p /sbin/ldconfig

%postun -n libwsman1 -p /sbin/ldconfig

%post server
/sbin/ldconfig
%systemd_post openwsmand.service

%preun server
%systemd_preun openwsmand.service

%postun server
rm -f /var/log/wsmand.log
%systemd_postun_with_restart openwsmand.service
/sbin/ldconfig

%post client -p /sbin/ldconfig

%postun client -p /sbin/ldconfig

%files -n libwsman1
%doc COPYING
%{_libdir}/libwsman.so.*
%{_libdir}/libwsman_client.so.*
%{_libdir}/libwsman_curl_client_transport.so.*

%if %{without pam}
%exclude %{_exec_prefix}/lib/debug/usr/lib64/ruby/vendor_ruby/_openwsman.so*
%exclude %{_libdir}/ruby/vendor_ruby/_openwsman.so
%exclude %{_datadir}/ruby/vendor_ruby/%{name}/%{name}.rb
%exclude %{_datadir}/ruby/vendor_ruby/%{name}/version.rb
%exclude %{_datadir}/ruby/vendor_ruby/%{name}/xmldoc.rb
%exclude %{_datadir}/ruby/vendor_ruby/%{name}/xmlnode.rb
%{_sysconfdir}/pam.d/openwsman
%{_exec_prefix}/lib/debug%{python2_sitearch}/_pywsman.so*
%{python2_sitearch}/_pywsman.so
%{python2_sitearch}/pywsman.py
%{python2_sitearch}/pywsman.pyc
%{python2_sitearch}/pywsman.pyo

%endif

%files -n libwsman-devel
%{_includedir}/*
%{_libdir}/pkgconfig/*
%{_libdir}/*.so

%files python3
%if %{with pam}
%{python3_sitearch}/*.so
%{python3_sitearch}/*.py
%{python3_sitearch}/__pycache__/*
%endif

%if %{with pam}
%files ruby
%dir %{gem_instdir}
%exclude %{gem_instdir}/ext
%{gem_libdir}
%{gem_extdir_mri}
%exclude %{gem_cache}
%{gem_spec}

%files ruby-docs
%doc %{gem_docdir}

%endif


%files perl
%{perl_vendorarch}/openwsman.so
%{perl_vendorlib}/openwsman.pm

%files server
# Don't remove *.so files from the server package.
# the server fails to start without these files.
%dir %{_sysconfdir}/openwsman
%config(noreplace) %{_sysconfdir}/openwsman/openwsman.conf
%config(noreplace) %{_sysconfdir}/openwsman/ssleay.cnf
%attr(0755,root,root) %{_sysconfdir}/openwsman/owsmangencert.sh
%attr(0755,root,root) %{_sysconfdir}/openwsman/owsmantestcert.sh
%if %{with pam}
%config(noreplace) %{_sysconfdir}/pam.d/openwsman
%endif
%{_unitdir}/openwsmand.service
%dir %{_libdir}/openwsman
%dir %{_libdir}/openwsman/authenticators
%{_libdir}/openwsman/authenticators/*.so
%{_libdir}/openwsman/authenticators/*.so.*
%dir %{_libdir}/openwsman/plugins
%{_libdir}/openwsman/plugins/*.so
%{_libdir}/openwsman/plugins/*.so.*
%{_sbindir}/openwsmand
%{_libdir}/libwsman_server.so.*

%files client
%{_libdir}/libwsman_clientpp.so.*
%config(noreplace) %{_sysconfdir}/openwsman/openwsman_client.conf

%files winrs
%{_bindir}/winrs

%files help
%doc AUTHORS ChangeLog README.md TODO
%{_mandir}/man8/*

%changelog
* Fri Feb 28 2020 likexin <likexin4@huawei.com> - 2.6.5-11
- update release 

* Thu Feb 13 2020 fengbing <fengbing7@huawei.com> - 2.6.5-10
- Type:N/A
- ID:N/A
- SUG:N/A
- DESC:fix build fail

* Fri Nov 29 2019 mengxian <mengxian@huawei.com> - 2.6.5-9
- OpenEuler package init
