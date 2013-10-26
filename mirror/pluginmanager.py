#
# Copyright (C) 2013 Shang Yuanchun <idealities@gmail.com>
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


import logging
import mirror.configmanager

log = logging.getLogger(__name__)

class PluginManager(object):

    def __init__(self, config_file, entry_name):
        self.config     = mirror.configmanager.ConfigManager(config_file)
        self.entry_name = entry_name

        self.plugins    = {}
        self.hooks      = {}

        self.scan_plugins()

    def enable_plugins(self):
        pass

    def enable_plugin(self, plugin_name):
        pass

    def disable_plugins(self):
        pass

    def disable_plugin(self, plugin_name):
        pass

    def scan_plugins():
        pass
