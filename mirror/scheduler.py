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
from mirror.task          import PRIORITY_MIN, PRIORITY_MAX
from mirror.sysinfo       import loadavg, tcpconn

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
        # the number of tasks that enabled
        self.active_tasks = -1

        self.init_general(self.config)
        self.init_tasks  (self.config)

        schedulers[os.getpid()] = weakref.ref(self)

    def start(self):
        while (True):
            self.sleep()
            log.info("I am waking up...")
            self.schedule()

    def sleep(self):
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

    def schedule(self):
        self.init_sysinfo()

        if ( self.todo & self.SCHEDULE_TASK):
            if not len(self.mirrors) > 0:
                log.info("But no task needed to start...")
                return
            # we do not need microseconds
            timestamp  = int(time.time())
            # to move to zero second
            timestamp -= timestamp % 60
            # next miniute
            end        = timestamp + 60
            for mirror in self.mirrors:
                if self.queue[mirror] < timestamp:
                    log.info("Strange problem happened,"
                             "task: %s schedule time is in past,"
                             "maybe I sleeped too long...", mirror)
                    del self.queue[mirror]
                    self.append_task(mirror, self.tasks[mirror], since = end)
                if self.queue[mirror] >= end:
                    return
                if self.queue[mirror] >= timestamp and self.queue[mirror] < end:
                    self.schedule_task(mirror)

    def schedule_task(self, mirror):
        """
        Schedule a task, but it is not guaranteed that it will really be run, it is 
        decided by some conditions, e.g. system load, current http connections.

        NOTE:
        The priority that a task can run is a function of ( current value / limit ).
        See get_runnable_priority(). However an exception is `maxtasks`, if current
        running tasks is reaching `maxtasks`, only specific priority (lower then or
        equal with 2) tasks can still be running.

        """
        task = self.tasks[mirror]
        if task.priority > self.get_runnable_priority(self.current_load, self.loadlimit):
            log.info("Task: %s not scheduled because system load %.2f is too high",
                     mirror, self.current_load)
            self.delay_task(mirror)
            return
        if task.priority > self.get_runnable_priority(self.current_conn,  self.httpconn):
            log.info("Task: %s not scheduled because http connections is too many",
                     mirror)
            self.delay_task(mirror)
            return
        if self.maxtasks > 0 and self.count_running_tasks() >= self.maxtasks and task.pririty > 2:
            log.info("Task: %s not scheduled because running tasks is larger than %d",
                     mirror, self.maxtasks)
            self.delay_task(mirror)
            return
        log.info("Starting task: %s ...", mirror)
        self.run_task(mirror)

    def init_sysinfo(self):
        """
        Get system info for this turn of schedule().

        """
        self.current_load = loadavg()
        self.current_conn = tcpconn()

    def delay_task(self, mirror, delay_seconds=1800):
        """
        If a task if not scheduled due to some reason, it will be 
        delayed for `delay_seconds` seconds (wich is default half
        an hour, if task's next schedule time is later than that, 
        else it's set to task's next schedule time.

        """
        if mirror not in self.queue:
            return
        task      = self.tasks[mirror]
        next_time = task.get_schedule_time(since = time.time())
        if self.queue[mirror] + delay_seconds > next_time:
            self.queue[mirror]  = next_time
        else:
            self.queue[mirror] += delay_seconds

    def count_running_tasks(self):
        """
        Calculate the number of current running tasks.

        """
        if self.active_tasks >= 0:
            return self.active_tasks - len(self.queue)
        running = 0
        for mirror, task in self.tasks.iteritems():
            running += task.running
        return running

    def append_tasks(self):
        """
        Append the tasks that are need to run into self.queue.

        NOTE:
        If a task is currently running or it is not enabled, it will
        not be added to the queue.

        """
        now = time.time()
        for mirror in self.tasks:
            if mirror in self.queue:
                continue
            task = self.tasks[mirror]
            self.append_task(mirror, task, since = now)

    def append_task(self, mirror, task, since):
        """
        In some cases a mirror task may be ignored if there is a running one,
        but this is a feature, not a bug...

        """
        if task.running:
            return
        if not task.enabled:
            return
        self.queue[mirror] = task.get_schedule_time(since)

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
        self.active_tasks = len(
                            [mirror for mirror, task in self.tasks.iteritems() if task.enabled])

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

    def stop_task_with_pid(self, pid, status):
        for mirror, task in self.tasks.iteritems():
            if task.pid == pid:
                task.set_stop_flag()
                log.info("Task: %s ended with status %d", mirror, status)
                return

    def stop_all_tasks(self, signo = signal.SIGTERM):
        """
        This method can only be called when mirrord is shut down by SIGTERM or SIGINT.

        NOTE:
        Currently when mirrord is shut down, all running tasks will also be killed.

        """
        for mirror, task in self.tasks.iteritems():
            if not task.running:
                continue
            pid = task.pid
            task.stop(signo)
            # Not sure it is ok...
            pid, status = os.waitpid(pid, 0)
            log.info("Killed task: %s with pid %d", mirror, pid)

    def get_runnable_priority(self, current, limit):
        """
        If limit is zero, all priority tasks can be run.
        Else if current value is lower than limit, all priority tasks can be run.
        Else it is a function between target priority and (current / limit).

        """
        if limit <= 0:
            return PRIORITY_MAX
        if current < limit:
            return PRIORITY_MAX
        return (-4.55 * (current * 1.0 / limit)) + 14.55

# Store Scheduler instance
schedulers = {}
