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
import importlib.metadata
import mirror.common
import mirror.configmanager
import mirror.component as component
from mirror.component import Component

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
        self.config = mirror.configmanager.ConfigManager(config_file)
        self.entry_name = entry_name

        self.available_plugins = []

        self.plugins = {}
        self.hooks = {}

        self.plugin_distributions = {}
        self.scan_plugins()

    def enable_plugins(self):
        for name in self.available_plugins:
            self.enable_plugin(name)

    def enable_plugin(self, plugin_name):
        if plugin_name in self.plugins:
            log.warn("Cannot enable an already enabled plugin %s", plugin_name)
            return

        plugin_name_key = plugin_name.replace(" ", "-")

        if plugin_name_key not in self.plugin_distributions:
            log.error("Plugin %s not found in scanned plugins", plugin_name)
            return

        dist = self.plugin_distributions[plugin_name_key]

        entry_points_list = [
            ep for ep in dist.entry_points if ep.group == self.entry_name
        ]

        for entry_point in entry_points_list:
            try:
                cls = entry_point.load()
                if not cls.enabled:
                    continue
                instance = cls(plugin_name_key.replace("-", "_"))
            except Exception as e:
                log.error(
                    "Unable to instantiate plugin %r from %r!",
                    entry_point.name,
                    dist.locate_file(""),
                )
                log.exception(e)
                continue
            instance.enable()
            if not instance.__module__.startswith("mirror.plugins."):
                log.warn("Wrong module for plugin: %s", entry_point.name)

            component.start([instance.plugin.name])
            plugin_name_display = plugin_name_key.replace("-", " ")
            self.plugins[plugin_name_display] = instance
            log.info("Plugin %s enabled...", plugin_name_display)

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
        Scans for available plugins using importlib.metadata
        """
        for dist in importlib.metadata.distributions():
            entry_points_list = [
                ep for ep in dist.entry_points if ep.group == self.entry_name
            ]

            if not entry_points_list:
                continue

            plugin_name = dist.metadata.get("Name", "")
            if not plugin_name:
                continue

            self.plugin_distributions[plugin_name] = dist

            log.debug(
                "Found plugin: %s %s at %s",
                plugin_name,
                dist.version,
                dist.locate_file("") if dist.locate_file else "unknown",
            )
            self.available_plugins.append(plugin_name)

    def __getitem__(self, key):
        return self.plugins[key]

    def get_available_plugins(self):
        return self.available_plugins

    def get_enabled_plugins(self):
        return list(self.plugins)

    def get_plugin_info(self, name):
        info = dict.fromkeys(METADATA_KEYS)

        name_key = name.replace(" ", "-")
        if name_key not in self.plugin_distributions:
            return info

        dist = self.plugin_distributions[name_key]
        metadata = dist.metadata

        key_mapping = {
            "Name": "Name",
            "License": "License",
            "Author": "Author",
            "Home-page": "Home-page",
            "Summary": "Summary",
            "Platform": "Platform",
            "Version": "Version",
            "Author-email": "Author-email",
            "Description": "Description",
        }

        for key in METADATA_KEYS:
            if metadata:
                value = metadata.get(key, "")
                info[key] = value if value else ""

        return info

    def start(self):
        self.enable_plugins()

    def stop(self):
        self.disable_plugins()
