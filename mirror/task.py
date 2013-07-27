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

log = logging.getLogger(__name__)

class Task(object):
    def __init__(self, name, command, **taskinfo):
        self.name    = name
        self.command = command
        self.enabled = True
        self.args    = "--links --hard-links --times --verbose --delete --recursive"
        try:
            self.upstream = taskinfo['upstream']
            self.rsyncdir = taskinfo['rsyncdir']
            self.localdir = taskinfo['localdir']
            self.twostage = taskinfo['twostage'] != "0" 
            self.timeout  = self.parse_timeout(taskinfo['timeout'])
        except KeyError, e:
            log.error("Error in config for mirror: %s, key: %s not found.", self.name, e)
            self.enabled = False
        try:
            self.priority = int(taskinfo['priority'])
        except:
            log.error("Error in config for mirror: %s, priority not valid.", self.name)
            self.priority = 0
        self.exclude  = taskinfo['exclude'] if taskinfo.has_key("exclude") else None
        self.args     = taskinfo['args']    if taskinfo.has_key("args")    else self.args
        if self.twostage and not taskinfo.has_key("firststage"):
            log.error("Error in config for mirror: %s, `twostage` is set but no `firststage`.", self.name)
            self.twostage = False

    def run(self):
        pass

    def execute(self):
        pass

    def get_schedule_time(self):
        pass
