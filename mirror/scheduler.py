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
import mirror.common
import mirror.error
import mirror.configmanager

from collections import OrderedDict as odict

log = logging.getLogger(__name__)

class Scheduler(object):
    def __init__(self, options=None, args=None):
        self.rsync   = mirror.common.find_rsync()
        if not self.rsync:
            raise mirror.error.MirrorError(
                "rsync nor found in PATH, please install rsync :)"
            )
        self.queue   = odict()
        self.running = {}

    def start(self):
        while (True):
            time.sleep(5)
            log.info("mirror is still alive...")

    def run_task(self, mirror):
        pass

    def stop_task(self, mirror):
        if mirror not in self.running:
            return
        pid = self.running.get(mirror)['pid']
        os.kill(pid, signal.SIGTERM)
        log.info("Killed mirror: %s with pid %d", mirror, pid)
