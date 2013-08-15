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
import signal
import logging
from mirror.scheduler import schedulers

log = logging.getLogger(__name__)

signals = { getattr(signal, sigtxt) : sigtxt
            for sigtxt in dir(signal) if sigtxt.startswith("SIG") }

def shutdown_handler(signo, frame):
    import mirror.configmanager
    pidfile = mirror.configmanager.get_config_dir("mirrord.pid")
    if os.path.isfile(pidfile):
        os.remove(pidfile)
    log.info("Got signal %s, exiting...", signals[signo])

    import sys
    scheduler_ref = schedulers.get(os.getpid(), None)
    if scheduler_ref is None:
        sys.exit(0)
    scheduler     = scheduler_ref()

    # We will waitpid() in stop_all_tasks(),
    # so unregister sigchld_handler here.
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    scheduler.stop_all_tasks()

    if hasattr(scheduler, "buspid"):
        os.kill(scheduler.buspid, signal.SIGTERM)
        pid, status = os.waitpid(scheduler.buspid, 0)
        log.info("Killed mirror dbus with pid: %d", pid)

    log.info("Bye bye... :)")
    sys.exit(0)

def sigchld_handler(signo, frame):
    try:
        pid, status = os.waitpid(-1, os.WNOHANG)
    except OSError,e:
        log.error("Error occured when waitpid(), %s.", e)
        return
    scheduler_ref = schedulers.get(os.getpid(), None)
    if scheduler_ref is None:
        return
    scheduler     = scheduler_ref()
    scheduler.stop_task_with_pid(pid, status)
