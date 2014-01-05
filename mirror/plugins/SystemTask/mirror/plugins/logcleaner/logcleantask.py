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
import glob
import time
import logging
import mirror.component as component
from mirror.task import SystemTask
from datetime    import datetime

_name = "logcleaner"

log = logging.getLogger(_name)

class LogCleanTask(SystemTask):

    def __init__(self):
        # Actually the `priority` here is meaningless
        taskinfo = { "time": "0 1 * * *", "priority": 6 }
        super(LogCleanTask, self).__init__(_name, None, **taskinfo)

    def run(self):
        scheduler = component.get("Scheduler")
        logdir    = scheduler.logdir

        now       = datetime.now()
        paths     = glob.glob(os.path.join(logdir, '*'))
        for path in paths:
            try:
                datestr = path.split('.')[-1]
                date    = time.strptime(datestr, "%Y-%m-%d")
                delta   = now - datetime.fromtimestamp(time.mktime(date))
                if delta.days > 10:
                    os.unlink(path)
            except Exception, e:
                log.exception(e)
            else:
                log.info("Deleted log file: %s", path)

