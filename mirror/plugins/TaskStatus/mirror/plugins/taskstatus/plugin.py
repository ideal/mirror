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
import time
import json
import logging
import mirror.component as component
from mirror.pluginbase import PluginBase
from collections import OrderedDict as odict

_plugin_name = "taskstatus"

log = logging.getLogger(_plugin_name)

_rsync_error = { 0:  "Sync succeed",
                 1:  "Syntax or usage error",
                 2:  "Protocol incompatibility",
                 3:  "Errors selecting input/output files, dirs",
                 4:  "Requested  action not supported",
                 5:  "Error starting client-server protocol",
                 6:  "Daemon unable to append to log-file",
                10:  "Error in socket I/O",
                11:  "Error in file I/O",
                12:  "Error in rsync protocol data stream",
                13:  "Errors with program diagnostics",
                14:  "Error in IPC code",
                20:  "Received SIGUSR1 or SIGINT",
                21:  "Some error returned by waitpid()",
                22:  "Error allocating core memory buffers",
                23:  "Partial transfer due to error",
                24:  "Partial transfer due to vanished source files",
                25:  "The --max-delete limit stopped deletions",
                30:  "Timeout in data send/receive",
                35:  "Timeout waiting for daemon connection",
               }

class Plugin(PluginBase):

    DEFAULT_STATUS_FILE = "/home/mirror/status/task_status.json"

    STATUS_INITIAL  = 0
    STATUS_RUNNING  = 1
    STATUS_FINISHED = 2

    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def enable(self):
        plugin_manager = component.get("PluginManager")
        config = plugin_manager.config

        try:
            self.status_file = config[_plugin_name]["status_file"]
        except:
            self.status_file = Plugin.DEFAULT_STATUS_FILE
            log.info(("Didn't set `status_file` in plugin.ini in `%s` section"
                      ", use default one: %s"), _plugin_name, self.status_file)

        self.enabled = True
        status_dir   = os.path.dirname(self.status_file)
        if not os.path.exists(status_dir):
            try:
                os.makedirs(status_dir)
            except:
                self.enabled = False
                log.warning("Create directory failed: %s", status_dir)

        event_manager  = component.get("EventManager")
        event_manager.register_event_handler("TaskEnqueueEvent",
                                             self.__on_task_enqueue)
        event_manager.register_event_handler("TaskStartEvent",
                                             self.__on_task_start)
        event_manager.register_event_handler("TaskStopEvent",
                                             self.__on_task_stop)

    def disable(self):
        pass

    def __on_task_enqueue(self, taskname):
        if not self.enabled:
            return

        scheduler = component.get("Scheduler")
        taskinfo  = scheduler.queue.find(taskname)
        status    = { "schedule": time.strftime(self.DATE_FORMAT,
                                       time.localtime(taskinfo.time)) }
        self.__set_task_status(taskname, status, overwrite = False)

    def __on_task_start(self, taskname, pid):
        if not self.enabled:
            return

        status = { "status": self.STATUS_RUNNING,
                   "date": time.strftime(self.DATE_FORMAT,
                                         time.localtime())}
        self.__set_task_status(taskname, status)

    def __on_task_stop(self, taskname, pid, exitcode):
        if not self.enabled:
            return

        scheduler = component.get("Scheduler")
        task = scheduler.tasks.get(taskname, None)
        if not task:
            return
        status = { "status": self.STATUS_FINISHED }
        if task.cmdname == "rsync":
            status["message"] = _rsync_error[exitcode]
        else:
            status["message"] = "Task finished"

        status["exitcode"] = exitcode
        status["date"] = time.strftime(self.DATE_FORMAT)

        taskinfo = scheduler.queue.find(taskname)
        if taskinfo:
            status["schedule"] = time.strftime(self.DATE_FORMAT,
                                      time.localtime(taskinfo.time))
        else:
            status["schedule"] = "Unknown"

        self.__set_task_status(taskname, status)

    def __set_task_status(self, taskname, status, overwrite = True):
        scheduler = component.get("Scheduler")
        task = scheduler.tasks.get(taskname)
        # We do not export internal task's status
        if task.isinternal:
            return

        # Add info about upstream
        if task.__class__.__name__ == "Task":
            status['upstream'] = task.upstream[0] + '::' + task.rsyncdir + '/'

        # Read old status file content
        try:
            fp = open(self.status_file, "r+" if os.path.exists(self.status_file) else "w+")
        except:
            log.warning("Open file failed: %s", self.status_file)
            return
        task_status = fp.read().rstrip("\r\n")
        if task_status:
            try:
                task_status = json.loads(task_status)
            except Exception as e:
                log.warning("Parse json file(%s) failed: %s", self.status_file, e)
                task_status = {}
        else:
            task_status = {}

        if overwrite:
            task_status[taskname] = status
        else:
            if taskname in task_status:
                task_status[taskname]["schedule"] = status["schedule"]
            else:
                status["status"] = self.STATUS_INITIAL
                task_status[taskname] = status

        if len(task_status) > 1:
            task_status = odict(sorted(task_status.iteritems()))
        fp.seek(0)
        try:
            fp.write(json.dumps(task_status, indent = 2))
        except Exception as e:
            log.exception(e)
            fp.truncate(0)
        else:
            fp.truncate()
        fp.close()
