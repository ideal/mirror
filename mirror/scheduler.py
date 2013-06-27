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
import logging
import fcntl
import mirror.configmanager

log = logging.getLogger(__name__)

class Scheduler(object):
    def __init__(self, options=None, args=None):
        pid     = None
        pidfile = mirror.configmanager.get_config_dir("mirrord.pid")
        if os.path.isfile(pidfile):
            try:
                pid = int(open(pidfile).read().strip())
            except:
                pass

        def is_process_running(pid):
            try:
                os.kill(pid, 0)
            except OSError:
                return False
            else:
                return True

        if pid and is_process_running(pid):
            raise mirror.error.MirrordRunningError("Another mirrord is running with pid: %d", pid)

        """Actually the code below is needless..."""
        try:
            fp = open(pidfile, "r+" if os.path.isfile(pidfile) else "w+")
        except IOError:
            raise mirror.error.MirrorError("Can't open or create %s", pidfile)

        try:
            fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except:
            raise mirror.error.MirrorError("Can't lock %s", pidfile)

        fcntl.fcntl(fp, fcntl.F_SETFD, 1)
        fp.write("%d\n" % os.getpid())
        fp.flush()

    def start(self):
        while (True):
            time.sleep(5)
            log.info("mirror is still alive...")
