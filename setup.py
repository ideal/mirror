#!/usr/bin/env python
#
# setup.py
#
# Copyright (C) 2013 Shang Yuanchun <idealities@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, write to:
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA    02110-1301, USA.
#

try:
    from setuptools import setup, find_packages, Extension
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages, Extension

import os, sys
import msgfmt
import platform

from distutils import cmd
from distutils.command.build import build as _build
from distutils.command.clean import clean as _clean

python_version = platform.python_version()[0:3]

class build_trans(cmd.Command):
    description = 'Compile .po files into .mo file'

    user_options = [
            ('build-lib', None, "lib build folder"),
            ('develop-mode', 'D', 'Compile translations in develop mode(into mirror/i18n')
    ]
    boolean_options = ['develop_mode']

    def initialize_options(self):
        self.build_lib = None
        self.develop_mode = False

    def finalize_options(self):
        self.set_undefined_options('build', ('build_lib', 'build_lib'))

    def run(self):
        po_dir = os.path.join(os.path.dirname(__file__), 'mirror/i18n/')

        if self.develop_mode:
            basedir = po_dir
        else:
            basedir = os.path.join(self.build_lib, 'mirror', 'i18n')

        print('Compiling po files from %s...' % po_dir),
        for path, names, filenames in os.walk(po_dir):
            for f in filenames:
                uptodate = False
                if f.endswith('.po'):
                    lang = f[:len(f) - 3]
                    src = os.path.join(path, f)
                    dest_path = os.path.join(basedir, lang, 'LC_MESSAGES')
                    dest = os.path.join(dest_path, 'mirror.mo')
                    if not os.path.exists(dest_path):
                        os.makedirs(dest_path)
                    if not os.path.exists(dest):
                        sys.stdout.write('%s, ' % lang)
                        sys.stdout.flush()
                        msgfmt.make(src, dest)
                    else:
                        src_mtime = os.stat(src)[8]
                        dest_mtime = os.stat(dest)[8]
                        if src_mtime > dest_mtime:
                            sys.stdout.write('%s, ' % lang)
                            sys.stdout.flush()
                            msgfmt.make(src, dest)
                        else:
                            uptodate = True
                if uptodate:
                    sys.stdout.write(' po files already up to date.  ')
        sys.stdout.write('\b\b \nFinished compiling translation files. \n')


class build(_build):
    sub_commands = [('build_trans', None), ] + _build.sub_commands
    def run(self):
        # Run all sub-commands (at least those that need to be run)
        _build.run(self)

class clean(_clean):
    sub_commands = _clean.sub_commands

    def run(self):
        # Run all sub-commands (at least those that need to be run)
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)
        _clean.run(self)

cmdclass = {
    'build': build,
    'build_trans': build_trans,
    'clean': clean,
}

# Data files to be installed to the system
_data_files = [
    ('share/man/man1', ['docs/man/mirror.1']),
	('/etc', ['config/mirror.ini'])
]

entry_points = {
    "console_scripts": [
		"mirror  = mirror.main:start",
        "mirrord = mirror.main:start_daemon"
    ],
}

# Main setup
setup(
    name = "mirror",
    version = "0.6.0",
    fullname = "Mirror for open source mirror site",
    description = "Mirror for open source mirror site to sync files",
    author = "Shang Yuanchun",
    author_email = "idealities@gmail.com",
    keywords = "open source mirror",
    long_description = """Mirror is for open source mirror site.""",
    url = "http://mirror.bjtu.edu.cn",
    license = "GPLv3",
    cmdclass = cmdclass,
    data_files = _data_files,
    package_data = {"mirror": [
                               "i18n/*/LC_MESSAGES/*.mo",
                               ]},
    packages = find_packages(exclude=["docs",]),
    namespace_packages = ["mirror",],
    entry_points = entry_points
)
