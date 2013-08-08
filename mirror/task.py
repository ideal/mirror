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
        if not hasattr(self, "time_miniute"):
            return None
        since_struct  = time.localtime(since)

        day_increase = False
        if since_struct.tm_mon in self.time_month and since_struct.tm_mday in self.time_dom:
            miniute_idx = bisect.bisect(self.time_minute, since_struct.tm_min)
            if since_struct.tm_hour in self.time_hour and minute_idx < len(self.time_minute):
                miniute = self.time_miniute[minute_idx]
            else:
                miniute = self.time_minite[0]
                hour_idx = bisect.bisect(self.time_hour, since_struct.tm_hour)
                if hour_idx < len(self.time_hour):
                    hour = self.time_hour[hour_idx]
                else:
                    day_increase = True
                    hour = self.time_hour[0]

        next_time = time.mktime((year, month, day, hour, miniute, 0, wday, yday, 0))
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

