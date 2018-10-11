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


import os
import logging
import pkg_resources
import mirror.common
import mirror.configmanager
import mirror.component as component
from   mirror.component import Component

log = logging.getLogger("pluginmanager")

METADATA_KEYS = (
    "Name",
    "License",
    "Author",
    "Home-page",
    "Summary",
    "Platform",
    "Version",
    "Author-email",
    "Description",
)

class PluginManager(Component):

    def __init__(self, config_file, entry_name):
        super(PluginManager, self).__init__(PluginManager.__name__)
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
        if plugin_name in self.plugins:
            log.warn("Cannot enable an already enabled plugin %s", plugin_name)
            return

        plugin_name = plugin_name.replace(' ', '-')
        egg         = self.pkg_env[plugin_name][0]
        egg.activate()
        for name in egg.get_entry_map(self.entry_name):
            entry_point = egg.get_entry_info(self.entry_name, name)
            try:
                cls      = entry_point.load()
                if not cls.enabled:
                    continue
                instance = cls(plugin_name.replace('-', '_'))
            except Exception as e:
                log.error("Unable to instantiate plugin %r from %r!",
                          name, egg.location)
                log.exception(e)
                continue
            instance.enable()
            if not instance.__module__.startswith("mirror.plugins."):
                log.warn("Wrong module for plugin: %s", name)

            component.start([instance.plugin.name])
            plugin_name = plugin_name.replace('-', ' ')
            self.plugins[plugin_name] = instance
            log.info("Plugin %s enabled...", plugin_name)

    def disable_plugins(self):
        plugin_names = list(self.plugins)
        for name in plugin_names:
            self.disable_plugin(name)

    def disable_plugin(self, plugin_name):
        if plugin_name not in self.plugins:
            log.info("Plugin %s is not enabled, no need to disable", plugin_name)
            return

        instance = self.plugins[plugin_name]
        instance.disable()
        component.deregister(instance)
        self.plugins.pop(plugin_name)

    def scan_plugins(self):
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

    def __getitem__(self, key):
        return self.plugins[key]

    def get_available_plugins(self):
        return self.available_plugins

    def get_enabled_plugins(self):
        return list(self.plugins)

    def get_plugin_info(self, name):
        info = dict.fromkeys(METADATA_KEYS)
        last_header = ""
        cont_lines  = []
        for line in self.pkg_env[name][0].get_metadata("PKG-INFO").splitlines():
            if not line:
                continue
            if line[0] in ' \t' and (
                len(line.split(":", 1)) == 1 or line.split(":", 1)[0] not in info):
                # This is a continuation
                cont_lines.append(line.strip())
            else:
                if cont_lines:
                    info[last_header] = "\n".join(cont_lines).strip()
                    cont_lines = []
                if line.split(":", 1)[0] in info:
                    last_header = line.split(":", 1)[0]
                    info[last_header] = line.split(":", 1)[1].strip()

        return info

    def start(self):
        self.enable_plugins()

    def stop(self):
        self.disable_plugins()

