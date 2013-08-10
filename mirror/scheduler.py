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


"""Scheduler for Mirror :("""

import os, sys
import time
import signal
import logging
import weakref
import mirror.common
import mirror.error
from mirror.configmanager import ConfigManager
from mirror.task          import Task

from collections import OrderedDict as odict

log = logging.getLogger(__name__)

class Scheduler(object):
    CHECK_TIMEOUT = 0x01
    SCHEDULE_TASK = 0x02

    def __init__(self, options=None, args=None):
        self.rsync   = mirror.common.find_rsync()
        if not self.rsync:
            raise mirror.error.MirrorError(
                "rsync not found in PATH, please install rsync :)"
            )
        # tasks contains all mirrors needed to rsync
        self.config  = ConfigManager("mirror.ini")
        self.tasks   = odict()
        self.queue   = {}
        self.todo    = self.SCHEDULE_TASK

        self.init_general(self.config)
        self.init_tasks  (self.config)

    def start(self):
        while (True):
            self.append_tasks()
            self.mirrors = sorted(self.queue, key = self.queue.get)
            # without timeout checking, self.queue[mirror] - time.time() is
            # the duration we can sleep...
            if len(self.mirrors) > 0:
                mirror    = self.mirrors[0]
                sleeptime = self.queue[mirror] - time.time()
            else:
                sleeptime = 5
            log.info("I am going to sleep, next waking up: %s",
                     time.ctime(time.time() + sleeptime))
            time.sleep(sleeptime)
            log.info("I am waking up...")
            self.schedule()

    def schedule(self):
        if ( self.todo & self.SCHEDULE_TASK):
            if not len(self.mirrors) > 0:
                log.info("But no task needed to start...")
                return
            timestamp  = self.queue[self.mirrors[0]]
            for mirror in self.mirrors:
                if self.queue[mirror] > timestamp:
                    continue
                log.info("Starting task: %s ...", mirror)
                self.run_task(mirror)

    def append_tasks(self):
        now = time.time()
        for mirror in self.tasks:
            if mirror in self.queue:
                continue
            task = self.tasks[mirror]
            if task.running:
                continue
            self.queue[mirror] = task.get_schedule_time(now)

    def init_general(self, config):
        self.emails    = []
        self.loadlimit = 4.0
        self.httpconn  = 1200
        self.logdir    = "/var/log/rsync"
        self.maxtasks  = 10

        if "general" not in config:
            log.error("Error in config file, no `general` section, will use default setting.")
            return
        import re
        emails = re.compile(r"([^@\s]+@[^@\s,]+)")
        emails = emails.findall(config['general']['emails'])
        for email in emails:
            self.emails.append(email)
        self.loadlimit = float(config['general']['loadlimit'])
        self.httpconn  = int  (config['general']['httpconn'] )
        self.maxtasks  = int  (config['general']['maxtasks'] )
        self.logdir    = config['general']['logdir']
        if self.logdir[-1] != os.path.sep:
            self.logdir += os.path.sep

    def init_tasks(self, config):
        for mirror in config:
            if mirror == 'general':
                continue
            self.tasks[mirror] = Task(mirror, self.rsync, weakref.ref(self), **config[mirror])

    def run_task(self, mirror):
        if mirror not in self.tasks:
            return
        task = self.tasks[mirror]
        if task.running:
            return
        task.run()
        if mirror in self.queue:
            del self.queue[mirror]
        log.info("Task: %s begin to run with pid %d", mirror, task.pid)

    def stop_task(self, mirror):
        if mirror not in self.tasks:
            return
        task = self.tasks[mirror]
        if not task.running:
            return
        pid  = task.pid
        task.stop()
        log.info("Killed task: %s with pid %d", mirror, pid)
