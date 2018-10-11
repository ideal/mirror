#
# Copyright (C) 2013-2014 Shang Yuanchun <idealities@gmail.com>
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
from mirror.pluginbase import PluginBase
from . import logcleantask
from . import taskcleantask

_plugin_name = "systemtask"

log = logging.getLogger(_plugin_name)

class SystemTask(PluginBase):

    def enable(self):
        event_manager  = component.get("EventManager")
        event_manager.register_event_handler("MirrorStartEvent",
                                             self.__on_mirror_start)
        event_manager.register_event_handler("RunSystemTaskEvent",
                                             self.__run_log_cleaner)
        self.logclean_task = logcleantask.LogCleanTask()

        event_manager.register_event_handler("RunSystemTaskEvent",
                                             self.__run_task_cleaner)
        self.taskclean_task = taskcleantask.TaskCleanTask()

    def disable(self):
        pass

    def __on_mirror_start(self):
        """
        NOTE: However currently SystemTask is run in plugin thread,
        and the Scheduler sleeps before SystemTask is appended into
        the queue, so SystemTask will only begin to take effect on
        next sleep loop.
        However for most system tasks, this is acceptable.

        """
        self.scheduler = component.get("Scheduler")

        self.scheduler.tasks[logcleantask._name] = self.logclean_task
        self.scheduler.active_tasks += 1
        log.info("Task: %s added", logcleantask._name)

        self.scheduler.tasks[taskcleantask._name] = self.taskclean_task
        self.scheduler.active_tasks += 1
        log.info("Task: %s added", taskcleantask._name)

    def __run_log_cleaner(self, taskinfo):
        # FIXME: need a better way
        if taskinfo.name != logcleantask._name:
            return

        log.info("Running task: %s", taskinfo.name)
        self.logclean_task.run()
        log.info("Finished task: %s", taskinfo.name)

    def __run_task_cleaner(self, taskinfo):
        # FIXME: need a better way
        if taskinfo.name != taskcleantask._name:
            return

        log.info("Running task: %s", taskinfo.name)
        self.taskclean_task.run()
        log.info("Finished task: %s", taskinfo.name)

