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
import pkg_resources
import mirror.common
import mirror.configmanager

log = logging.getLogger(__name__)

METADATA_KEYS = (
    "Name",
    "License",
    "Author",
    "Homepage",
    "Summary",
    "Platform",
    "Version",
    "Author-email",
    "Description",
)

class PluginManager(object):

    def __init__(self, config_file, entry_name):
        self.config     = mirror.configmanager.ConfigManager(config_file)
        self.entry_name = entry_name

        # available plugins
        self.available_plugins = []

        # enabled plugins
        self.plugins    = {}
        self.hooks      = {}

        self.scan_plugins()

    def enable_plugins(self):
        for name in self.available_plugins:
            self.enable_plugin(name)

    def enable_plugin(self, plugin_name):
        plugin_name = plugin_name.replace(' ', '-')

    def disable_plugins(self):
        for name in self.plugins:
            self.disable_plugin(name)

    def disable_plugin(self, plugin_name):
        pass

    def scan_plugins():
        """
        Scans for available plugins

        """
        base_plugin_dir = mirror.common.resource_filename("mirror", "plugins")
        pkg_resources.working_set.add_entry(base_plugin_dir)
        user_plugin_dir = os.path.join(mirror.configmanager.get_config_dir(), "plugins")

        plugins_dirs    = [ base_plugin_dir ]
        for dirname in os.listdir(base_plugin_dir):
            plugin_dir  = os.path.join(base_plugin_dir, dirname)
            pkg_resources.working_set.add_entry(plugin_dir)
            plugins_dirs.append(plugin_dir)

        pkg_resources.working_set.add_entry(user_plugin_dir)
        plugins_dirs.append(user_plugin_dir)

        self.pkg_env    = pkg_resources.Environment(plugins_dirs)

        for name in self.pkg_env:
            log.debug("Found plugin: %s %s at %s",
                       self.pkg_env[name][0].project_name,
                       self.pkg_env[name][0].version,
                       self.pkg_env[name][0].location)
            self.available_plugins.append(self.pkg_env[name][0].project_name)
