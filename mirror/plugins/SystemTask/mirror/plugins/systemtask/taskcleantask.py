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
import time
import signal
import logging
import mirror.component as component
from mirror.task import SystemTask

_name = "taskcleaner"

log = logging.getLogger(_name)

class TaskCleanTask(SystemTask):

    # For those tasks which have no time out set,
    # we will check it after 10 days.
    TASK_TIMEOUT = 864000

    def __init__(self):
        # Actually the `priority` here is meaningless
        taskinfo = { "time": "0 2 * * *", "priority": 6 }
        super(TaskCleanTask, self).__init__(_name, None, **taskinfo)

        self.timeout_days = self.TASK_TIMEOUT / (24 * 3600)

    def run(self):
        scheduler = component.get("Scheduler")

        curtime   = time.time()
        for taskname, task in scheduler.tasks.iteritems():
            try:
                # internal tasks have no `running`
                if not hasattr(task, "running"):
                    continue
                if not task.running:
                    continue
                # SIGCHLD will trigger in main thread
                if curtime - task.start_time > self.TASK_TIMEOUT:
                    os.kill(task.pid, signal.SIGTERM)
                    log.info("Killed task: %s, whose life exceeds %d days",
                             taskname, self.timeout_days)
            except Exception, e:
                log.exception(e)

