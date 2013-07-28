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
    def __init__(self, options=None, args=None):
        self.rsync   = mirror.common.find_rsync()
        if not self.rsync:
            raise mirror.error.MirrorError(
                "rsync nor found in PATH, please install rsync :)"
            )
        # tasks contains all mirrors needed to rsync
        self.config  = ConfigManager("mirror.ini")
        self.tasks   = odict()

        self.init_general(self.config)
        self.init_tasks(self.config)

        self.running = {}

    def start(self):
        while (True):
            time.sleep(5)
            log.info("mirror is still alive...")

    def init_general(self, config):
        self.emails    = []
        self.loadlimit = 4.0
        self.httpconn  = 1200
        self.logdir    = "/var/log/rsync"

        if "general" not in config:
            log.error("Error in config file, no `general` section, will use default setting.")
            return
        import re
        emails = re.compile("([^@\s]+@[^@\s,]+)")
        emails = emails.findall(config['general']['emails'])
        for email in emails:
            self.emails.append(email)
        self.loadlimit = float(config['general']['loadlimit'])
        self.httpconn  = int(config['general']['httpconn'])
        self.logdir    = config['general']['logdir']
        if self.logdir[-1] != os.path.sep:
            self.logdir += os.path.sep

    def init_tasks(self, config):
        for mirror in config:
            if mirror == 'general':
                continue
            self.tasks[mirror] = Task(mirror, self.rsync, weakref.ref(self), **config[mirror])

    def run_task(self, mirror):
        os.execv(self.rsync, ["rsync"])

    def stop_task(self, mirror):
        if mirror not in self.running:
            return
        pid = self.running.get(mirror)['pid']
        os.kill(pid, signal.SIGTERM)
        log.info("Killed mirror: %s with pid %d", mirror, pid)
