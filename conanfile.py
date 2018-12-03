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
    requires = "sip/4.19.13@zehome/testing"
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
                self.run("{vc}python configure.py --confirm-license "
                    "--no-timestamp --no-designer-plugin --disable=QtNfc "
                    "--qmake={qmake} -c -j{cpucount} --no-dist-info "
                    "--stubsdir={stubsdir} "
                    "--bindir={bindir} "
                    "--destdir={destdir} "
                    "--sipdir={sipdir} "
                    "--sip-incdir={sipincdir}".format(
                        cpucount=tools.cpu_count(),
                        vc="{0} && ".format(vcvars) if vcvars is not None else '',
                        bindir=os.path.join(self.build_folder, "bin"),
                        incdir=os.path.join(self.build_folder, "include"),
                        sipdir=os.path.join(self.build_folder, "sip", "PyQt5"),
                        destdir=os.path.join(self.build_folder, "site-packages"),
                        stubsdir=os.path.join(self.build_folder, "site-packages", "PyQt5"),
                        sipincdir=sipincdir,
                    )
                )
                if self.settings.os == "Windows":
                    vcvars = tools.vcvars_command(self.settings)
                    self.run("{0} && jom".format(vcvars))
                    self.run("{0} && jom install".format(vcvars))
                else:
                    self.run("make -j{}".format(tools.cpu_count()))
                    self.run("make install")

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
