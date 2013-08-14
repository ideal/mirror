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
import sys
import time
import bisect
import signal
import logging
import mirror.common

log = logging.getLogger(__name__)

DEFAULT_ARGS = "--links --hard-links --times --verbose --delete --recursive"

PRIORITY_MIN = 1  # high priority
PRIORITY_MAX = 10 # low  priority

REGULAR_TASK = 1  # regular task
TIMEOUT_TASK = 2  # timeout checking task

class AbstractTask(object):
    def __init__(self, name, scheduler_ref=None, **taskinfo):
        self.scheduler = (scheduler_ref() if scheduler_ref is not None else None)
        self.name      = name
        self.enabled   = True

        if taskinfo.get("command", None) == None:
            log.warn("In config for task: %s, key: command not found, "
                     "using rsync as default",
                     name)
            command = "rsync"
        else:
            command = taskinfo.get("command")
        # NOTE: `command` is just a command name, but
        # self.command is the complete path...
        self.command   = mirror.common.find_command(command)
        if not self.command:
            log.error("command `%s` not found in PATH, please install that first :)",
                      command)
            self.enabled = False
        self.running   = False
        self.pid       = 0
        self.stage     = 1
        try:
            self.twostage = taskinfo['twostage'] != "0" 
            self.timeout  = mirror.common.parse_timeout(taskinfo['timeout'])
            self.time     = taskinfo['time']
        except KeyError, e:
            log.error("Error in config for task: %s, key: %s not found.", self.name, e)
            self.enabled  = False

        try:
            self.priority = int(taskinfo['priority'])
            if self.priority < PRIORITY_MIN:
                self.priority = PRIORITY_MIN
            if self.priority > PRIORITY_MAX:
                self.priority = PRIORITY_MAX
        except:
            log.error("Error in config for task: %s, priority not valid.", self.name)
            self.priority = PRIORITY_MAX

        if self.twostage and not taskinfo.has_key("firststage"):
            log.error("Error in config for task: %s, `twostage` is set but no `firststage`.", self.name)
            self.twostage = False
        if self.twostage:
            self.firststage = taskinfo['firststage']
        crontime = mirror.common.parse_cron_time(self.time)
        if crontime:
            self.time_miniute = crontime[0]
            self.time_hour    = crontime[1]
            self.time_dom     = crontime[2]
            self.time_month   = crontime[3]
            self.time_dow     = crontime[4]
            for attr in ('time_miniute', 'time_hour', 'time_dom', 'time_month', 'time_dow'):
                if len(getattr(self, attr)) == 0:
                    log.error("Error in config for task: %s, time: %s not valid.", self.name, attr)
                    self.enabled = False
        else:
            log.error("Error in config for task: %s, time not valid.")
            self.enabled = False

    def run(self, stage = 1):
        try:
            self.stage = stage
            self.execute(stage)
        except Exception, e:
            log.error("Error occured when run `%s`: %s.", self.name, e)
            # If fork succeed but error occured before execv, we need to exit child process
            if os.getpid() == self.pid:
                sys.exit(1)
            # If we are in parent process, e.g. scheduler
            self.pid     = 0
            self.running = False

    def execute(self, stage):
        pid = os.fork()
        if pid > 0:
            self.pid        = pid
            self.running    = True
            self.start_time = int(time.time())
        elif pid == 0:
            self.pid   = os.getpid()
            if self.scheduler:
                logdir = self.scheduler.logdir
            else:
                logdir = mirror.common.DEFAULT_TASK_LOG_DIR
            fp = open(logdir + self.name + '.log.' + time.strftime('%Y-%m-%d'), 'a')
            # Redirect child process's stdout and stderr
            os.dup2(fp.fileno(), 1)
            os.dup2(fp.fileno(), 2)
            fp.close()
            os.execv(self.command, self.get_args(stage))

    def stop(self, signo = signal.SIGTERM):
        if self.pid > 0:
            os.kill(self.pid, signo)
        self.set_stop_flag()

    def set_stop_flag(self):
        self.pid     = 0
        self.running = False

    TIME_STRUCT  = 1
    TIME_SECONDS = 2

    def get_schedule_time(self, since, style=TIME_SECONDS):
        """
        This method is too long.

        """

        if not hasattr(self, "time_miniute"):
            return None
        if not self.enabled:
            return None
        since_struct  = time.localtime(since)

        miniute = since_struct.tm_min
        hour    = since_struct.tm_hour
        day     = since_struct.tm_mday
        month   = since_struct.tm_mon
        year    = since_struct.tm_year

        day_increase   = False
        month_increase = False
        year_increase  = False
        if since_struct.tm_mon in self.time_month and since_struct.tm_mday in self.time_dom:
            miniute_idx = bisect.bisect(self.time_miniute, since_struct.tm_min)
            if since_struct.tm_hour in self.time_hour and miniute_idx < len(self.time_miniute):
                miniute = self.time_miniute[miniute_idx]
                hour    = since_struct.tm_hour
            else:
                miniute  = self.time_miniute[0]
                hour_idx = bisect.bisect(self.time_hour, since_struct.tm_hour)
                if hour_idx < len(self.time_hour):
                    hour = self.time_hour[hour_idx]
                else:
                    hour = self.time_hour[0]
                    day_increase = True
            if len(self.time_miniute) == 60 and len(self.time_hour) != 24:
                miniute  = self.time_miniute[0]
                hour_idx = bisect.bisect(self.time_hour, since_struct.tm_hour)
                if hour_idx < len(self.time_hour):
                    hour = self.time_hour[hour_idx]
                else:
                    hour = self.time_hour[0]
                    day_increase = True
            if not day_increase:
                day   = since_struct.tm_mday
                month = since_struct.tm_mon
        if since_struct.tm_mday not in self.time_dom or day_increase:
            miniute = self.time_miniute[0]
            hour    = self.time_hour[0]
            day_idx = bisect.bisect(self.time_dom, since_struct.tm_mday)
            if day_idx < len(self.time_dom):
                day = self.time_dom[day_idx]
            else:
                day = self.time_dom[0]
                month_increase = True
            if not month_increase:
                month = since_struct.tm_mon
        if since_struct.tm_mon not in self.time_month or month_increase:
            miniute = self.time_miniute[0]
            hour    = self.time_hour[0]
            day     = self.time_dom[0]
            month_idx = bisect.bisect(self.time_month, since_struct.tm_mon)
            if month_idx < len(self.time_month):
                month = self.time_month[month_idx]
            else:
                month = self.time_month[0]
                year_increase = True
        if year_increase:
            year += 1

        next_time   = time.mktime((year, month, day, hour, miniute, 0, 0, 0, 0))
        next_struct = time.localtime(next_time)
        if (next_struct.tm_wday + 1) not in self.time_dow:
            from datetime import datetime, timedelta
            wday_idx = bisect.bisect(self.time_dow, next_struct.tm_wday)
            if wday_idx < len(self.time_dow):
                wdays = self.time_dow[wday_idx] - next_struct.tm_wday
            else:
                wdays = (7 - self.time_dow[-1]) + self.time_dow[0]
            delta = timedelta(days = wdays)
            next_time = time.mktime((datetime.fromtimestamp(next_time) + delta).timetuple())

        if style == self.TIME_SECONDS:
            return next_time
        else:
            return time.localtime(next_time)

    def get_args(self, stage = 1):
        raise MirrorError("AbstractTask's get_args() is not implemented.")

class Task(AbstractTask):
    def __init__(self, name, scheduler_ref=None, **taskinfo):
        super(Task, self).__init__(name, scheduler_ref, **taskinfo)

        try:
            self.upstream = taskinfo['upstream[]']
            self.rsyncdir = taskinfo['rsyncdir']
            if self.rsyncdir[-1] != '/':
                self.rsyncdir += '/'
            self.localdir = taskinfo['localdir']
        except KeyError, e:
            log.error("Error in config for mirror: %s, key: %s not found.", self.name, e)
            self.enabled  = False

        self.exclude  = taskinfo['exclude'] if taskinfo.has_key("exclude") else None
        self.args     = taskinfo['args']    if taskinfo.has_key("args")    else DEFAULT_ARGS

    def get_args(self, stage = 1):
        args  = [os.path.basename(self.command)]
        args += self.args.split(" ")
        if self.exclude:
            args += self.exclude.split(" ")
        if self.twostage and stage == 1:
            args += [self.upstream[0] + '::' + self.rsyncdir + self.firststage + '/',\
                     self.localdir + '/' + self.firststage]
            return args
        if self.twostage and stage == 2:
            args += ['--exclude', '/' + self.firststage + '/']
        args += [self.upstream[0] + '::' + self.rsyncdir,\
                 self.localdir]
        return args

class SimpleTask(AbstractTask):
    def __init__(self, name, scheduler_ref=None, **taskinfo):
        super(SimpleTask, self).__init__(name, scheduler_ref, **taskinfo)

        """
        If a SimpleTask is twostage, args is interpreted as args for second
        stage, firststage is interpreted as args for first stage.

        """
        self.args = taskinfo['args'] if taskinfo.has_key("args") else None

    def get_args(self, stage = 1):
        args  = [os.path.basename(self.command)]
        if self.twostage and stage == 1:
            args += self.firststage.split(" ")
            return args
        if self.args:
            args += self.args.split(" ")
        return args

# from name to Task
TASK_TYPES = { "simple" : SimpleTask }

if __name__ == "__main__":
    import mirror.log
    mirror.log.setupLogger(level="info",
                           filename="/home/ideal/.config/mirror/mirrord.log",
                           filemode="a")
    from mirror.configmanager import ConfigManager
    config = ConfigManager("mirror.ini")
    task   = Task('archlinux', None, **config['archlinux'])

    # The date to Shanghai
    since  = time.mktime((2013, 7, 20, 8, 0, 0, 0, 0, 0))
    print(time.ctime(task.get_schedule_time(since)))
    print(task.get_args())
    #task.run()
    #time.sleep(100)

    task   = Task('ubuntu', None, **config['ubuntu'])
    print(time.ctime(task.get_schedule_time(time.time())))
    print(task.get_args())
    print(task.get_args(stage=2))
