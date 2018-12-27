#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools
import os
import shutil


class PyQtConan(ConanFile):
    name = "PyQt5"
    version = "5.11.3"
    description = "Python binding for Qt5"
    topics = "conan", "python", "binding", "sip", "qt"
    url = "https://github.com/zehome/conan-pyqt5"
    homepage = "https://www.riverbankcomputing.com/software/pyqt/"
    author = "Laurent Coustet <ed@zehome.com>"
    license = "GPL-3.0-only"
    generators = "txt"
    settings = "os", "compiler", "build_type", "arch"
    requires = "sip/4.19.13@clarisys/stable", "qt/5.12.0@bincrafters/stable"
    options = {'shared': [True, False]}
    default_options = 'shared=True'
    exports_sources = ("pyqt5_init.py", )
    # Repackage sip
    keep_imports = True
    _source_subfolder = "pyqt-src"

    def source(self):
        source_url = "https://sourceforge.net/projects/pyqt/files/PyQt5"
        tools.get("{0}/PyQt-{1}/PyQt5_gpl-{1}.tar.gz".format(source_url, self.version))
        extracted_dir = "{0}_gpl-{1}".format(self.name, self.version)
        if os.path.exists(self._source_subfolder):
            shutil.rmtree(self._source_subfolder)
        os.rename(extracted_dir, self._source_subfolder)

    def build_requirements(self):
        if tools.os_info.is_windows and self.settings.compiler == "Visual Studio":
            self.build_requires("jom_installer/1.1.2@bincrafters/stable")

    def build(self):
        with tools.chdir(self._source_subfolder):
            if self.settings.os == "Windows":
                vcvars = tools.vcvars_command(self.settings)
                envappend = {"CXXFLAGS": "/bigobj"}
            else:
                vcvars = None
                envappend = {}
            sipincdir = None
            for incdir in self.deps_cpp_info["sip"].include_paths:
                if "sip.h" in os.listdir(incdir):
                    sipincdir=incdir
                    break
            if sipincdir is None:
                raise Exception("sip.h not found")
            with tools.environment_append(envappend):
                # QtNfc does not build on windows, disable it
                self.run("{vc}python configure.py --confirm-license {static}"
                    "--no-timestamp --no-designer-plugin --disable=QtNfc "
                    "-c -j{cpucount} --no-dist-info "
                    "--stubsdir={stubsdir} "
                    "--bindir={bindir} "
                    "--destdir={destdir} "
                    "--sipdir={sipdir} "
                    "--qtconf-prefix={qtconf_prefix} "
                    "--sip-incdir={sipincdir}".format(
                        cpucount=tools.cpu_count(),
                        vc="{0} && ".format(vcvars) if vcvars is not None else '',
                        static="--static " if not self.options.shared else '',
                        bindir=os.path.join(self.build_folder, "bin"),
                        incdir=os.path.join(self.build_folder, "include"),
                        sipdir=os.path.join(self.build_folder, "sip", "PyQt5"),
                        destdir=os.path.join(self.build_folder, "site-packages"),
                        stubsdir=os.path.join(self.build_folder, "site-packages", "PyQt5"),
                        sipincdir=sipincdir,
                        # LC: This is critical to building python wheel package
                        # it will register an embedded version of qt.conf
                        # which will have prefix set to Qt\, from the root of
                        # the PyQt5 package.
                        # You can check QResource: QtCore.QResource("qt/etc/qt.conf").data()
                        qtconf_prefix="Qt", 
                    ),
                    run_environment=True,
                )
                if self.settings.os == "Windows":
                    vcvars = tools.vcvars_command(self.settings)
                    self.run("{0} && jom".format(vcvars), run_environment=True)
                    self.run("{0} && jom install".format(vcvars), run_environment=True)
                else:
                    self.run("make -j{}".format(tools.cpu_count()), run_environment=True)
                    self.run("make install", run_environment=True)
        shutil.copyfile("pyqt5_init.py", os.path.join(self.build_folder, "site-packages", "PyQt5", "__init__.py"))

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        self.copy("*", src="bin", dst="bin")
        self.copy("*", src="sip", dst="sip")
        self.copy("*", src="site-packages", dst="site-packages")
        self.copy("*.h", src="include", dst="include")

    def imports(self):
        self.copy("*", src="site-packages", dst="site-packages", root_package="sip")

    def package_info(self):
        self.env_info.path.append(os.path.join(self.package_folder, "bin"))
        self.env_info.pythonpath.append(os.path.join(self.package_folder, "site-packages"))
