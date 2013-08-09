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
import bisect
import logging
import mirror.common

log = logging.getLogger(__name__)

DEFAULT_ARGS = "--links --hard-links --times --verbose --delete --recursive"

class Task(object):
    def __init__(self, name, command, scheduler_ref=None, **taskinfo):
        self.scheduler = (scheduler_ref() if scheduler_ref is not None else None)
        self.name      = name
        self.command   = command
        self.enabled   = True
        self.running   = False
        try:
            self.upstream = taskinfo['upstream[]']
            self.rsyncdir = taskinfo['rsyncdir']
            if self.rsyncdir[-1] != '/':
                self.rsyncdir += '/'
            self.localdir = taskinfo['localdir']
            self.twostage = taskinfo['twostage'] != "0" 
            self.timeout  = mirror.common.parse_timeout(taskinfo['timeout'])
            self.time     = taskinfo['time']
        except KeyError, e:
            log.error("Error in config for mirror: %s, key: %s not found.", self.name, e)
            self.enabled  = False
        try:
            self.priority = int(taskinfo['priority'])
        except:
            log.error("Error in config for mirror: %s, priority not valid.", self.name)
            self.priority = 10
        self.exclude  = taskinfo['exclude'] if taskinfo.has_key("exclude") else None
        self.args     = taskinfo['args']    if taskinfo.has_key("args")    else DEFAULT_ARGS
        if self.twostage and not taskinfo.has_key("firststage"):
            log.error("Error in config for mirror: %s, `twostage` is set but no `firststage`.", self.name)
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
                    log.error("Error in config for mirror: %s, time: %s not valid.", self.name, attr)
                    self.enabled = False
        else:
             self.enabled = False

    def run(self, stage = 1):
        try:
            self.execute(stage)
        except Exception, e:
            log.error("Error occured when run `%s`: %s.", self.name, e)
            self.running = False
            self.pid     = 0

    def execute(self, stage):
        pid = os.fork()
        if pid > 0:
            self.running = True
            self.pid     = pid
            self.start_time = time.time()
        elif pid == 0:
            if self.scheduler:
                fp = open(scheduler.logdir + self.name + '.log.' + time.strftime('%Y-%m-%d'), 'a')
                os.dup2(fp.fileno(), 1)
                os.dup2(fp.fileno(), 2)
                fp.close()
            os.execv(self.command, self.get_args(stage))

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
        args  = [os.path.basename(self.command)]
        args += self.args.split(" ")
        args += self.exclude.split(" ")
        if self.twostage and stage == 1:
            args += [self.upstream[0] + '::/' + self.rsyncdir + self.firststage + '/',\
                     self.localdir + '/' + self.firststage]
            return args
        if self.twostage and stage == 2:
            args += ['--exclude', '/' + self.firststage + '/']
        args += [self.upstream[0] + '::/' + self.rsyncdir,\
                 self.localdir]
        return args

if __name__ == "__main__":
    from mirror.configmanager import ConfigManager
    config = ConfigManager("mirror.ini")
    task   = Task('archlinux', '/usr/bin/rsync', None, **config['archlinux'])

    since  = time.mktime((2013, 7, 31, 23, 0, 0, 0, 0, 0))
    print(time.ctime(task.get_schedule_time(since)))
    print(task.get_args())
