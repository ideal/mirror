#
# Copyright (C) 2013 Shang Yuanchun <idealities@gmail.com>
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
import signal
import logging
import mirror.common
import mirror.error
import mirror.component as component

log = logging.getLogger(__name__)

signals = { getattr(signal, sigtxt) : sigtxt
            for sigtxt in dir(signal) if sigtxt.startswith("SIG") and
            not sigtxt.startswith("SIG_") }

def shutdown_handler(signo, frame):
    import mirror.configmanager
    pidfile = mirror.configmanager.get_config_dir("mirrord.pid")
    if os.path.isfile(pidfile):
        os.remove(pidfile)
    log.info("Got signal %s, exiting...", signals[signo])

    import sys
    scheduler = component.get("Scheduler")
    if scheduler is None:
        sys.exit(0)

    # We will waitpid() in stop_all_tasks(),
    # so unregister sigchld_handler here.
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    scheduler.stop_all_tasks()

    if hasattr(scheduler, "buspid"):
        os.kill(scheduler.buspid, signal.SIGTERM)
        pid, status = os.waitpid(scheduler.buspid, 0)
        log.info("Killed mirror dbus with pid: %d", pid)

    event_manager = component.get("EventManager")
    while (event_manager.plugin_thread and
           len(event_manager.plugin_thread.event_queue) > 0):
        time.sleep(0.1)
    component.deregister(event_manager)
    component.deregister(component.get("PluginManager"))

    # Deregister the scheduler,
    # this will call scheduler's stop().
    # But scheduler's start() is called
    # directly, not by component's start().
    component.deregister(scheduler)

    log.info("Bye bye... :)")
    sys.exit(0)

def sigchld_handler(signo, frame):
    try:
        pid, status = os.waitpid(-1, os.WNOHANG)
    except OSError as e:
        log.error("Error occured when waitpid(), %s.", e)
        return
    scheduler = component.get("Scheduler")
    if scheduler is None:
        return
    scheduler.stop_task_with_pid(pid, status)

    # In Python 3, execution of signal handler will not terminate the sleep() as Python 2
    # But it will still be terminated if signal handler raises an exception
    # For convenience, we raise en exception manually
    # https://mozillazg.com/2017/07/python-time-sleep-terminate-by-signal.html

    if mirror.common.is_python3():
        raise mirror.error.MirrordTaskFinishedFakeError("Task finished, please stop sleep")

def reload_handler(signo, frame):
    log.info("Got signal %s, start reloading...", signals[signo])
    scheduler = component.get("Scheduler")
    scheduler.reload_config()
