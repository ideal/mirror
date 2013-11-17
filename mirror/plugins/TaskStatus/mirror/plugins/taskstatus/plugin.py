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

import json
import logging
import mirror.component as component
from mirror.pluginbase import PluginBase

__plugin_name = "taskstatus"

log = logging.getLogger(__plugin_name)

class Plugin(PluginBase):

    DEFAULT_STATUS_FILE = "/home/mirror/status/task_status.json"

    def enable(self):
        plugin_manager = component.get("PluginManager")
        config = plugin_manager.config

        try:
            self.status_file = config(__plugin_name)["status_file"]
        except:
            self.status_file = Plugin.DEFAULT_STATUS_FILE
            log.info(("Didn't set `status_file` in plugin.ini in `%s` section"
                      ", use default one: %s"), __plugin_name, self.status_file)

        event_manager  = component.get("EventManager")
        event_manager.register_event_handler("TaskStartEvent",
                                             self.__on_task_start)
        event_manager.register_event_handler("TaskStopEvent",
                                             self.__on_task_stop)

    def disable(self):
        pass

    def __on_task_start(self, taskname, pid):
        pass

    def __on_task_stop(self, taskname, pid, exitcode):
        pass
