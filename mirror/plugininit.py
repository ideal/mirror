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

log = logging.getLogger(__name__)

class PluginInitBase(object):

    _plugin_class = None

    def __init__(self, plugin_name):
        self.plugin = self._plugin_class(plugin_name)

    def enable(self):
        try:
            self.plugin.enable()
        except Exception as e:
            log.error("Unable to enable plugin: %s", self.plugin.name)
            log.exception(e)

    def disable(self):
        try:
            self.plugin.disable()
        except Exception as e:
            log.error("Unable to disable plugin: %s", self.plugin.name)
            log.exception(e)
