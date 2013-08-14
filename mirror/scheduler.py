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
from mirror.task          import Task, SimpleTask, TASK_TYPES
from mirror.task          import PRIORITY_MIN, PRIORITY_MAX
from mirror.task          import REGULAR_TASK, TIMEOUT_TASK
from mirror.sysinfo       import loadavg, tcpconn
from mirror.queue         import TaskInfo, Queue

from collections import OrderedDict as odict

log = logging.getLogger(__name__)

class Scheduler(object):
    CHECK_TIMEOUT = 0x01
    SCHEDULE_TASK = 0x02

    def __init__(self, options = None, args = None):
        # self.tasks contains all tasks needed to run in theory,
        # including the tasks that are not enabled
        self.config  = ConfigManager("mirror.ini")
        self.tasks   = odict()
        self.queue   = Queue()
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

        taskinfo = self.queue[0]
        # taskinfo.time - time.time() is
        # the duration we can sleep...
        if taskinfo:
            sleeptime = taskinfo.time - time.time()
        else:
            sleeptime = 1800 # half an hour
        log.info("I am going to sleep, next waking up: %s",
                 time.ctime(time.time() + sleeptime))
        time.sleep(sleeptime)

    def schedule(self):
        if self.queue.empty():
            log.info("But no task needed to start...")
            return

        self.init_sysinfo()

        taskqueue  = [ taskinfo for taskinfo in self.queue ]
        if ( self.todo & self.SCHEDULE_TASK):
            # we do not need microseconds
            timestamp  = int(time.time())
            # to move to zero second
            timestamp -= timestamp % 60
            # next miniute
            end        = timestamp + 60
            for taskinfo in taskqueue:
                if taskinfo.tasktype != REGULAR_TASK:
                    continue
                if taskinfo.time < timestamp:
                    log.info("Strange problem happened,"
                             "task: %s schedule time is in past,"
                             "maybe I sleeped too long...", taskinfo.name)
                    self.queue.remove(taskinfo)
                    self.append_task(taskinfo.name, self.tasks[taskinfo.name], since = end)
                if taskinfo.time >= end:
                    break
                if taskinfo.time >= timestamp and taskinfo.time < end:
                    self.schedule_task(taskinfo)

    def schedule_task(self, taskinfo):
        """
        Schedule a task, but it is not guaranteed that it will really be run, it is 
        decided by some conditions, e.g. system load, current http connections.

        NOTE:
        The priority that a task can run is a function of ( current value / limit ).
        See get_runnable_priority(). However an exception is `maxtasks`, if current
        running tasks is reaching `maxtasks`, only specific priority (lower than or
        equal to 2) tasks can still be running.

        """
        task = self.tasks[taskinfo.name]
        if task.priority > self.get_runnable_priority(self.current_load, self.loadlimit):
            log.info("Task: %s not scheduled because system load %.2f is too high",
                     taskinfo.name, self.current_load)
            self.delay_task(taskinfo)
            return
        if task.priority > self.get_runnable_priority(self.current_conn,  self.httpconn):
            log.info("Task: %s not scheduled because http connections is too many",
                     taskinfo.name)
            self.delay_task(taskinfo)
            return
        if self.maxtasks > 0 and self.count_running_tasks() >= self.maxtasks and task.pririty > 2:
            log.info("Task: %s not scheduled because running tasks is larger than %d",
                     taskinfo, self.maxtasks)
            self.delay_task(taskinfo)
            return
        log.info("Starting task: %s ...", taskinfo.name)
        self.run_task(taskinfo)

    def init_sysinfo(self):
        """
        Get system info for this turn of schedule().

        """
        self.current_load = loadavg()
        self.current_conn = tcpconn()

    def delay_task(self, taskinfo, delay_seconds = 1800):
        """
        If a task is not scheduled due to some reason, it will be
        delayed for `delay_seconds` seconds (wich is default half
        an hour), when task's next schedule time is later than that,
        else it's set to task's next schedule time.

        """
        if taskinfo not in self.queue:
            return
        task      = self.tasks[taskinfo.name]
        next_time = task.get_schedule_time(since = time.time())
        if taskinfo.time + delay_seconds > next_time:
            taskinfo.time  = next_time
        else:
            # In python objects are passed by reference
            taskinfo.time += delay_seconds

    def count_running_tasks(self):
        """
        Calculate the number of current running tasks.

        """
        if self.active_tasks >= 0:
            return self.active_tasks - self.queue.size("type", REGULAR_TASK)
        running = 0
        for taskname, task in self.tasks.iteritems():
            running += task.running
        return running

    def append_tasks(self):
        """
        Append the tasks that are needed to run into self.queue.

        NOTE:
        If a task is currently running or it is not enabled, it will
        not be added to the queue.

        """
        now = time.time()
        for taskname in self.tasks:
            task = self.tasks[taskname]
            self.append_task(taskname, task, since = now)

    def append_task(self, taskname, task, since):
        """
        In some cases a task with same name may be ignored if there
        is a running one, but this is a feature, not a bug...

        """
        if task.running:
            return
        if not task.enabled:
            return
        taskinfo = TaskInfo(taskname, REGULAR_TASK, task.get_schedule_time(since))
        if taskinfo in self.queue:
            return
        self.queue.put(taskinfo)

    def append_timeout_task(self, taskname, task, time):
        """
        A timeout checking task is added after a task begins to run.

        """
        if not task.running:
            return
        if not task.enabled:
            return
        taskinfo = TaskInfo(taskname, TIMEOUT_TASK, time)
        if taskinfo in self.queue:
            return
        self.queue.put(taskinfo)

    def remove_timeout_task(self, taskname):
        """
        It's slow...

        """
        taskqueue  = [ taskinfo for taskinfo in self.queue ]
        for taskinfo in taskqueue:
            if taskinfo.name == taskname and taskinfo.tasktype == TIMEOUT_TASK:
                self.queue.remove(taskinfo)
                return

    def init_general(self, config):
        self.emails    = []
        self.loadlimit = 4.0
        self.httpconn  = 1200
        self.logdir    = mirror.common.DEFAULT_TASK_LOG_DIR
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
            # We think it's default mirror.task.Task
            task_class = TASK_TYPES.get(config[mirror].get("type", None), Task)
            self.tasks[mirror] = task_class(mirror, weakref.ref(self), **config[mirror])
        self.active_tasks = len(
                            [mirror for mirror, task in self.tasks.iteritems() if task.enabled])

    def run_task(self, taskinfo, stage = 1):
        if taskinfo.name not in self.tasks:
            return
        task = self.tasks[taskinfo.name]
        if task.running:
            return
        task.run(stage)
        if taskinfo in self.queue:
            self.queue.remove(taskinfo)
        log.info("Task: %s begin to run with pid %d", taskinfo.name, task.pid)
        if task.timeout <= 0:
            return
        self.append_timeout_task(taskinfo.name, task, task.start_time + task.timeout)

    def stop_task(self, taskinfo):
        """
        Stop a task, it should only be called when that task timeouts.

        """
        if taskinfo.name not in self.tasks:
            return
        task = self.tasks[taskinfo.name]
        if not task.running:
            return
        pid  = task.pid
        task.stop()
        log.info("Killed task: %s with pid %d", taskinfo.name, pid)
        if task.timeout > 0:
            self.remove_timeout_task(taskinfo.name)

    def stop_task_with_pid(self, pid, status):
        """
        Change task's running and pid attr as it's stopped.

        """
        for taskname, task in self.tasks.iteritems():
            if task.pid == pid:
                if not task.running:
                    return
                task.set_stop_flag()
                log.info("Task: %s ended with status %d", taskname, status)
                self.remove_timeout_task(taskname)
                self.task_post_process(task)
                return

    def task_post_process(self, task):
        """
        Check whether a task needs post process, e.g. two stage tasks.

        """
        if not task.twostage:
            return
        if task.stage == 1:
            log.info("Task: %s scheduled to second stage", task.name)
            self.run_task(TaskInfo(task.name, REGULAR_TASK, 0), stage = 2)
        else:
            task.stage = 1

    def stop_all_tasks(self, signo = signal.SIGTERM):
        """
        This method can only be called when mirrord is shut down by SIGTERM or SIGINT.

        NOTE:
        Currently when mirrord is shut down, all running tasks will also be killed.

        """
        for taskname, task in self.tasks.iteritems():
            if not task.running:
                continue
            pid = task.pid
            task.stop(signo)
            # Not sure it is ok...
            pid, status = os.waitpid(pid, 0)
            log.info("Killed task: %s with pid %d", taskname, pid)

    @classmethod
    def get_runnable_priority(cls, current, limit):
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
