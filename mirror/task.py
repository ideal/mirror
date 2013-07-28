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
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#

import os
import logging
import mirror.common

log = logging.getLogger(__name__)

DEFAULT_ARGS = "--links --hard-links --times --verbose --delete --recursive"

class Task(object):
    def __init__(self, name, command, scheduler_ref=None, **taskinfo):
        self.scheduler = scheduler_ref()
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
        elif pid == 0:
            os.execv(self.command, self.get_args(stage))

    def get_schedule_time(self):
        pass

    def get_args(self, stage = 1):
        args  = self.args.split(" ")
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

