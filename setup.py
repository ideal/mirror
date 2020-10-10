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

"""
Mirror is an open source python application for mirror site (e.g. mirror.bjtu.edu.cn)
to sync files from upstreams (it uses rsync internally), it actually works like a
cron, but still has some differences. It has been served for mirror.bjtu.edu.cn with
more than 40 rsync tasks.
"""

try:
    from setuptools import setup, find_packages, Extension
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages, Extension

import os, sys
import glob
import shlex
import msgfmt
import platform
import unittest

from distutils import cmd
from distutils.command.build import build as _build
from distutils.command.clean import clean as _clean

python_version = platform.python_version()[0:3]

class build_trans(cmd.Command):
    description = 'Compile .po files into .mo file'

    user_options = [
            ('build-lib=', None, "lib build folder"),
            ('develop-mode', 'D', 'Compile translations in develop mode(into mirror/i18n)')
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

class build_plugins(cmd.Command):
    description = "Build plugins into .eggs"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # Build the plugin eggs
        PLUGIN_PATH = "mirror/plugins/*"

        for path in glob.glob(PLUGIN_PATH):
            if os.path.exists(os.path.join(path, "setup.py")):
                os.system("cd " + path + " && " + sys.executable + " setup.py bdist_egg -d ..")


class build(_build):
    sub_commands = [ ('build_trans', None), ('build_plugins', None) ] + _build.sub_commands
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

class test(cmd.Command):
    """Command for running unittests without install."""

    user_options = [("args=", None, '''The command args string passed to
                                       unittest framework, such as
                                       --args="-v -f"''')]

    def initialize_options(self):
        self.args = ''

    def finalize_options(self):
        pass

    def run(self):
        self.run_command('build')
        bld = self.distribution.get_command_obj('build')
        # Add build_lib in to sys.path so that unittest can found DLLs and libs
        sys.path.insert(0, os.path.abspath(bld.build_lib))

        test_argv0 = [sys.argv[0] + ' test --args=']
        # For transfering args to unittest, we have to split args by ourself,
        # so that command like:
        #
        #   python setup.py test --args="-v -f"
        #
        # can be executed, and the parameter '-v -f' can be transfering to
        # unittest properly.
        test_argv = test_argv0 + shlex.split(self.args)
        unittest.main(None, defaultTest='test.test_suite', argv=test_argv)

cmdclass = {
    'build': build,
    'build_trans': build_trans,
    'build_plugins': build_plugins,
    'test': test,
    'clean': clean,
}

# Data files to be installed to the system
_data_files = [
    ('share/man/man1',   ['docs/man/mirrord.1']),
    ('share/mirror/etc', ['config/mirror.ini']),
    ('share/zsh/site-functions', ['completion/zsh/_mirrord']),
    ('share/bash-completion/completions', ['completion/bash/mirrord']),
    ('lib/systemd/system', ['util/systemd/system/mirrord@.service']),
    ('/var/log/mirrord', []),
    ('/var/log/rsync', []),
]

entry_points = {
    "console_scripts": [
        "mirrord = mirror.main:start_daemon"
    ],
}

this_directory = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

# Main setup
setup(
    name = "mirror",
    version = "0.8.2",
    fullname = "Mirror for open source mirror site",
    description = "Mirror for open source mirror site to sync files",
    author = "Shang Yuanchun, Bob Gao",
    author_email = "Shang Yuanchun <idealities@gmail.com>, Bob Gao <gaobo@bjtu.edu.cn>",
    keywords = "open source mirror",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url = "http://mirror.bjtu.edu.cn",
    license = "GPLv3",
    cmdclass = cmdclass,
    data_files = _data_files,
    package_data = {"mirror": [
                               "plugins/*.egg",
                               "i18n/*/LC_MESSAGES/*.mo",
                               ]},
    packages = find_packages(exclude=["completion", "docs", "test"]),
    python_requires = '>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    entry_points = entry_points
)
