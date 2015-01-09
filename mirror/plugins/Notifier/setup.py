#
# Copyright (C) 2013-2015 Shang Yuanchun <idealities@gmail.com>
#
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# mirror is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with mirror. If not, write to:
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA  02110-1301, USA.
#
#

from setuptools import setup, find_packages

__plugin_name__  = "Notifier"
__author__       = "Shang Yuanchun"
__author_email__ = "idealities@gmail.com"
__version__      = "0.1.9"
__url__          = "http://mirror.bjtu.edu.cn"
__license__      = "GPLv3"
__description__  = "Notifier plugin for mirror."
__long_description__ = """"""
__pkg_data__     = { 'mirror.plugins.' + __plugin_name__.lower(): [ "data/*" ] }

setup(
    name=__plugin_name__,
    version=__version__,
    description=__description__,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    license=__license__,
    long_description=__long_description__ if __long_description__ else __description__,
    packages=find_packages(),
    namespace_packages = ["mirror", "mirror.plugins"],
    package_data = __pkg_data__,

    entry_points="""
    [mirror.plugin.mirrorplugin]
    %s = mirror.plugins.%s:MirrorPlugin
    """ % (__plugin_name__, __plugin_name__.lower())
)
