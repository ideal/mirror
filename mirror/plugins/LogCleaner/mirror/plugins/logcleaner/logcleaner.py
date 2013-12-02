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
import mirror.component as component
import logcleantask
from mirror.pluginbase import PluginBase

_plugin_name = "logcleaner"

log = logging.getLogger(_plugin_name)

class LogCleaner(PluginBase):

    def enable(self):
        event_manager  = component.get("EventManager")
        event_manager.register_event_handler("MirrorStartEvent",
                                             self.__on_mirror_start)
        event_manager.register_event_handler("RunSystemTaskEvent",
                                             self.__run_log_cleaner)
        self.task = logcleantask.LogCleanTask()

    def disable(self):
        pass

    def __on_mirror_start(self):
        self.scheduler = component.get("Scheduler")
        self.scheduler.tasks[_plugin_name] = self.task
        self.scheduler.active_tasks += 1

    def __run_log_cleaner(self, taskinfo):
        log.info("Running task: %s", taskinfo.name)
        self.task.run()
        log.info("Finished task: %s", taskinfo.name)
