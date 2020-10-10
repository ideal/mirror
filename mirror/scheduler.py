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
import fcntl
import signal
import logging
import weakref
import mmap
import struct
try:
    import cPickle as pickle
except:
    import pickle

import mirror.common
import mirror.error
import mirror.handler
import mirror.event
import mirror.component   as     component
from mirror.configmanager import ConfigManager
from mirror.task          import Task, SimpleTask, TASK_TYPES
from mirror.task          import PRIORITY_MIN, PRIORITY_MAX
from mirror.task          import REGULAR_TASK, TIMEOUT_TASK, SYSTEM_TASK
from mirror.sysinfo       import loadavg, tcpconn
from mirror.queue         import TaskInfo, Queue
from mirror.component     import Component

from collections import OrderedDict as odict

log = logging.getLogger(__name__)

class Scheduler(Component):
    CHECK_TIMEOUT = 0x01
    SCHEDULE_TASK = 0x02

    def __init__(self, options = None, args = None):
        # The name is "Scheduler"
        super(Scheduler, self).__init__(self.__class__.__name__)
        # self.tasks contains all tasks needed to run in theory,
        # including the tasks that are not enabled
        self.config  = ConfigManager("mirror.ini")
        self.tasks   = odict()
        self.queue   = Queue()
        self.todo    = self.SCHEDULE_TASK
        # the number of tasks that enabled
        self.active_tasks    = -1
        self.expect_time     = 0
        self.roused_by_child = False

        self.init_general(self.config)
        self.init_tasks  (self.config)

    def start(self):
        event_manager = component.get("EventManager")
        event_manager.emit(mirror.event.MirrorStartEvent())
        while (True):
            self.sleep()
            if not self.roused_by_child:
                log.info("I am waking up...")
            self.schedule()

    TODO = { REGULAR_TASK : SCHEDULE_TASK,
             SYSTEM_TASK  : SCHEDULE_TASK,
             TIMEOUT_TASK : CHECK_TIMEOUT,
            }

    def sleep(self):
        # SIGCHLD may be coming before into sleep()
        # better need something like pselect() + sig_atomic_t
        try:
            self.append_tasks()
            self.write_mmap()

            nexttask  = self.queue[0]
            self.todo = 0
            if nexttask:
                for taskinfo in self.queue:
                    if taskinfo.time > nexttask.time:
                        break
                    self.todo |= self.TODO.get(taskinfo.tasktype, 0)
            # nexttask.time - time.time() is
            # the duration we can sleep...
            if nexttask:
                sleeptime = nexttask.time - time.time()
                # if system time is updated by ntpdate or other ways,
                # we may get a sleeptime < 0 and thus an "Invalid argument" error,
                # so we need to change it to a valid value
                sleeptime = 0 if sleeptime < 0 else sleeptime
            else:
                sleeptime = 1800 # half an hour
            log.info("I am going to sleep, next waking up: %s",
                     time.ctime(time.time() + sleeptime))
            self.expect_time     = int(time.time()) + sleeptime
            self.roused_by_child = False

            time.sleep(sleeptime)
        except mirror.error.MirrordTaskFinishedFakeError as e:
            pass

    def schedule(self):
        if self.queue.empty():
            log.info("But no task needed to start...")
            return

        self.init_sysinfo()

        curtime    = time.time()
        taskqueue  = [ taskinfo for taskinfo in self.queue ]

        # detect if time has been set back (e.g. by ntpdate) to the right value
        if (not self.roused_by_child and
                curtime < self.expect_time and self.todo & self.SCHEDULE_TASK):
            time_gap = self.expect_time - curtime
            for taskinfo in taskqueue:
                if self.TODO.get(taskinfo.tasktype, 0) != self.SCHEDULE_TASK:
                    continue
                taskinfo.time -= time_gap

        # we do not need microseconds
        curtime    = int(curtime)

        if ( self.todo & self.SCHEDULE_TASK ):
            # to move to zero second
            timestamp  = curtime
            timestamp -= curtime   % 60
            # next miniute
            end        = timestamp + 60
            for taskinfo in taskqueue:
                if self.TODO.get(taskinfo.tasktype, 0) != self.SCHEDULE_TASK:
                    continue
                if taskinfo.time < timestamp:
                    log.info("Strange problem happened,"
                             "task: %s schedule time is in past,"
                             "maybe because of system time changed, but it's also scheduled...", taskinfo.name)
                    self.schedule_task(taskinfo)
                if taskinfo.time >= end:
                    break
                if taskinfo.time >= timestamp and taskinfo.time < end:
                    self.schedule_task(taskinfo)

        if ( self.todo & self.CHECK_TIMEOUT ):
            for taskinfo in taskqueue:
                if self.TODO.get(taskinfo.tasktype, 0) != self.CHECK_TIMEOUT:
                    continue
                if taskinfo.time <= curtime:
                    log.info("Task: %s timeouts",
                             taskinfo.name)
                    self.stop_task(taskinfo)
                if taskinfo.time > curtime:
                    break

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
        if task.isinternal:
            self.run_system_task(taskinfo)
            return

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
        if self.maxtasks > 0 and self.count_running_tasks() >= self.maxtasks and task.priority > 2:
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
        self.reappend_task(task, taskinfo)

    def count_running_tasks(self):
        """
        Calculate the number of current running tasks.

        """
        running = 0
        for taskname, task in self.tasks.items():
            if task.isinternal:
                continue
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
        if task.running and task.timeout > 0:
            return
        if not task.enabled:
            return
        taskinfo = TaskInfo(taskname, (SYSTEM_TASK if task.isinternal else REGULAR_TASK),
                            task.get_schedule_time(since), task.priority)

        # for system tasks and tasks-without-timeout-set, task is appended again
        # in run_*_task() method, for tasks-with-timeout-set, a timeout task
        # with same name is appended in run_task()
        if taskinfo in self.queue:
            return
        self.queue.put(taskinfo)
        event_manager = component.get("EventManager")
        event_manager.emit(mirror.event.TaskEnqueueEvent(taskname))

    def reappend_task(self, task, taskinfo):
        """
        Remove a taskinfo from queue and put it in again,
        to keep the queue in order.

        """
        if taskinfo not in self.queue:
            return
        self.queue.remove(taskinfo)
        self.queue.put(taskinfo)
        event_manager = component.get("EventManager")
        event_manager.emit(mirror.event.TaskEnqueueEvent(taskinfo.name))

    DEFAULT_BUFFER_SIZE  = 10240

    def write_mmap(self):
        data = pickle.dumps(self.queue)
        size = len(data) + 2 + 4
        if not hasattr(self, "buffer") or self.buffersz < size:
            self.buffersz = max(self.DEFAULT_BUFFER_SIZE, size)
            if hasattr(self, "buffer"):
                self.buffer.close()
            self.bufferfd = os.open("/tmp/mirrord",
                                    os.O_CREAT | os.O_TRUNC | os.O_RDWR,
                                    0o644)
            flag = fcntl.fcntl(self.bufferfd, fcntl.F_GETFD)
            fcntl.fcntl(self.bufferfd, fcntl.F_SETFD, flag | fcntl.FD_CLOEXEC)
            os.write(self.bufferfd, b'\x00' * self.buffersz)
            self.buffer   = mmap.mmap(self.bufferfd, self.buffersz, mmap.MAP_SHARED, mmap.PROT_WRITE)
            # close bufferfd
            os.close(self.bufferfd)
            self.buffer.write(b"\x79\x71")
        self.buffer.seek(2)
        self.buffer.write(struct.pack("I", size))
        self.buffer.write(data)

    def stop(self):
        log.info("Stopping mirror scheduler")
        if not hasattr(self, "buffer"):
            return
        self.buffer.close()
        os.unlink("/tmp/mirrord")

    def append_timeout_task(self, taskname, task, time):
        """
        A timeout checking task is added after a task begins to run.

        """
        if not task.running:
            return
        if not task.enabled:
            return
        taskinfo = TaskInfo(taskname, TIMEOUT_TASK,
                            time, task.priority)
        if taskinfo in self.queue:
            return
        self.queue.put(taskinfo)
        event_manager = component.get("EventManager")
        event_manager.emit(mirror.event.TaskEnqueueEvent(taskname))

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

    def reload_config(self):
        log.info("Stopping running tasks...")
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)
        self.stop_all_tasks()
        signal.signal(signal.SIGCHLD, mirror.handler.sigchld_handler)

        log.info("Clearing old data...")
        self.tasks = odict(filter(lambda x:x[1].isinternal,self.tasks.items()))
        self.queue = Queue()

        log.info("Reloading new configs...")
        self.config = ConfigManager("mirror.ini", need_reload = True)
        self.init_general(self.config)
        self.init_tasks  (self.config)

    def init_tasks(self, config):
        for mirror in config:
            if mirror == 'general':
                continue
            # We think it's default mirror.task.Task
            task_class = TASK_TYPES.get(config[mirror].get("type", None), Task)
            self.tasks[mirror] = task_class(mirror, weakref.ref(self), **config[mirror])
        self.active_tasks = len(
                            [mirror for mirror, task in self.tasks.items() if task.enabled])

    def run_system_task(self, taskinfo):
        event_manager = component.get("EventManager")
        event_manager.emit(mirror.event.RunSystemTaskEvent(taskinfo))
        # after we run the system task, we need to update the queue
        # or else the sleeptime will be invalid
        if taskinfo in self.queue:
            self.queue.remove(taskinfo)
        task = self.tasks[taskinfo.name]
        self.append_task(taskinfo.name, task, time.time())

    def run_task(self, taskinfo, stage = 1):
        if taskinfo.name not in self.tasks:
            return
        task = self.tasks[taskinfo.name]
        # for tasks that is still running when next schedule time
        # is reached (but has no timeout set), we just need to
        # reappend it.
        if task.running and task.timeout <= 0:
            taskinfo.time  = task.get_schedule_time(since = time.time())
            self.reappend_task(task, taskinfo)
        if task.running and ( not task.twostage ):
            log.info("Task: %s is still running and no timeout set, skipped", taskinfo.name)
            return

        event_manager = component.get("EventManager")
        event_manager.emit(mirror.event.PreTaskStartEvent(taskinfo.name))
        task.run(stage)
        if taskinfo in self.queue:
            self.queue.remove(taskinfo)
        log.info("Task: %s begin to run with pid %d", taskinfo.name, task.pid)
        event_manager.emit(mirror.event.TaskStartEvent(taskinfo.name, task.pid))

        if task.timeout <= 0:
            self.append_task(taskinfo.name, task, time.time())
        else:
            self.append_timeout_task(taskinfo.name, task,
                                     task.start_time + task.timeout)

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
        # Python's SIGCHLD sometimes has delay in calling its handler,
        # we have to disable sigchld_handler() here.
        # More: http://utcc.utoronto.ca/~cks/space/blog/python/CPythonSignals
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)
        task.stop()
        self.stop_task_manually(task, pid)
        signal.signal(signal.SIGCHLD, mirror.handler.sigchld_handler)

    def stop_task_manually(self, task, pid):
        """
        Without SIGCHLD handler, we have to waitpid() here.

        """
        pid, status  = os.waitpid(pid, 0)
        endstr, code = self.parse_return_status(status)
        task.code    = code
        log.info("Killed task: %s %s %d, pid %d", task.name, endstr, code, pid)
        self.remove_timeout_task(task.name)
        self.task_finished(task)

    def stop_task_with_pid(self, pid, status):
        """
        This is called when we got a SIGCHLD signal.
        Change task's running and pid attr as it's stopped.

        """
        self.roused_by_child = True
        for taskname, task in self.tasks.items():
            if task.isinternal:
                continue
            if task.pid == pid:
                if not task.running:
                    return
                endstr, code = self.parse_return_status(status)
                task.code    = code
                log.info("Task: %s %s %d, pid %d", taskname, endstr, code, pid)
                self.remove_timeout_task(taskname)
                self.task_finished(task)
                return

    def task_finished(self, task):
        """
        Check whether a task needs post process, e.g. two stage tasks.

        """
        event_manager = component.get("EventManager")
        if not task.twostage:
            event_manager.emit(mirror.event.TaskStopEvent(task.name, task.pid, task.code))
            self.task_autoretry(task)
            task.set_stop_flag()
            return
        if task.stage == 1:
            log.info("Task: %s scheduled to second stage", task.name)
            self.run_task(TaskInfo(task.name, REGULAR_TASK, 0, task.priority), stage = 2)
        else:
            event_manager.emit(mirror.event.TaskStopEvent(task.name, task.pid, task.code))
            self.task_autoretry(task)
            task.set_stop_flag()
            task.stage = 1

    def task_autoretry(self, task):
        """
        If a task has a valid `autoretry`, and its interval is before next normal schedule,
        it will be used.

        """
        if task.autoretry <= 0:
            return
        if task.code == 0:
            return
        curtime   = int(time.time())
        next_time = task.get_schedule_time(since = curtime)
        if curtime + task.autoretry < next_time:
            taskinfo = self.queue[task.name]
            taskinfo.time = next_time
            self.reappend_task(task, taskinfo)

    def stop_all_tasks(self, signo = signal.SIGTERM):
        """
        This method can only be called when mirrord is shut down by SIGTERM or SIGINT.

        NOTE:
        Currently when mirrord is shut down, all running tasks will also be killed.

        """
        event_manager = component.get("EventManager")
        for taskname, task in self.tasks.items():
            if task.isinternal:
                continue
            if not task.running:
                continue
            pid = task.pid
            task.stop(signo)
            # Not sure it is ok...
            pid, status  = os.waitpid(pid, 0)

            endstr, code = self.parse_return_status(status)
            task.code    = code
            event_manager.emit(mirror.event.TaskStopEvent(task.name, task.pid, task.code))
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

    @classmethod
    def parse_return_status(cls, status):
        if (status & 0xff) != 0:
            endstr = "killed by signal"
            code   = (status & 0xff)
        else:
            endstr = "ended with return code"
            # See "EXIT VALUES" section in man rsync
            code   = (status >> 8)
        return (endstr, code)
