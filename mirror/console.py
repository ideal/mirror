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

import os, sys
import time
import mmap
import struct
import signal
try:
    import cPickle as pickle
except:
    import pickle

import mirror.color
import mirror.common
import mirror.task  as task
import mirror.error as error
from mirror.common import write_stderr

TASK_DESC = {
            task.REGULAR_TASK: "Normal task",
            task.TIMEOUT_TASK: "Timeout check",
            task.SYSTEM_TASK : "System task",
            }

def list_task_queue():
    try:
        bufferfd = os.open("/tmp/mirrord", os.O_RDONLY)
    except:
        write_stderr(_("Open /tmp/mirrord failed, "
                       "can't read task information, please make sure that mirrord is running"))
        return error.MIRROR_ERROR

    buffer = mmap.mmap(bufferfd, os.fstat(bufferfd).st_size,
                       mmap.MAP_SHARED, mmap.PROT_READ)
    os.close(bufferfd)
    if buffer[:2] != b'\x79\x71':
        write_stderr(_("Wrong file /tmp/mirrord, "
                       "any other wrote it?"))
        return error.MIRROR_ERROR

    buffer.seek(2)
    size = struct.unpack("I", buffer.read(4))[0]

    taskqueue = pickle.loads(buffer.read(size))
    formatstr = ("Task:"+mirror.color.FOREGROUND_COLORS.GREEN
                +"%-18s"+mirror.color.COLOR_RESET+"\ttype:%14s\ttime: %s")
    for taskinfo in taskqueue:
        print(formatstr % (
              taskinfo.name, TASK_DESC[taskinfo.tasktype],
              time.asctime(time.localtime(taskinfo.time))))

    buffer.close()
    return error.MIRROR_OK

signals = {
          "stop"  : signal.SIGQUIT,
          "reload": signal.SIGHUP,
          } if mirror.common.is_os_windows else {
          "stop"  : signal.SIGINT,
          }

def signal_process(signame):
    signames = signals.keys()
    if signame not in signames:
        write_stderr(_("Invalid value for -s, "
                       "available: ") + ", ".join(signames))
        return error.MIRROR_ERRARG
    import mirror.configmanager
    pidfile = mirror.configmanager.get_config_dir("mirrord.pid")
    pid = mirror.common.read_mirrord_pid(pidfile)
    if not pid:
        write_stderr(_("Can not read mirrord's pid, "
                       "please make sure that mirrord is running"))
        return error.MIRROR_ERROR
    try:
        os.kill(pid, signals.get(signame))
    except Exception as e:
        write_stderr(_("Kill mirrord (%d) failed: %s"),
                     pid, e)
        return error.MIRROR_ERROR

    return error.MIRROR_OK

