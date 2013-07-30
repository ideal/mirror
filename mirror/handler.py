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

log = logging.getLogger(__name__)

def shutdown_handler(signo, frame):
    import mirror.configmanager
    pidfile = mirror.configmanager.get_config_dir("mirrord.pid")
    if os.path.isfile(pidfile):
        os.remove(pidfile)
    log.info("Got signal %d, exiting... Bye bye", signo)
    import sys
    sys.exit(0)

def sigchld_handler(signo, frame):
    try:
        pid, status = os.waitpid(-1, os.WNOHANG)
    except OSError,e:
        log.error("Error occured when waitpid(), %s.", e)
        return
    scheduler = frame.f_globals.get('scheduler', None)
    if scheduler is None:
        return
