#
# Copyright (C) 2014 Shang Yuanchun <idealities@gmail.com>
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

import unittest
import time

from mirror.task import Task

class TaskTestCase(unittest.TestCase):

    def test_task(self):
        config = {
                 'upstream[]': 'mirror.bjtu.edu.cn',
                 'command': 'rsync',
                 'exclude': '',
                 'time':  '* */2 * * *',
                 'rsyncdir': 'archlinux/',
                 'localdir': '/tmp/mirror/archlinux',
                 'args': '--links --hard-links --times --verbose --delete --recursive',
                 'twostage': '0',
                 'timeout': '2h',
                 'priority': '2',
                 }
        task   = Task('archlinux', None, **config)
        since  = time.mktime((2013, 7, 20, 8, 0, 0, 0, 0, 0))
        self.assertEqual(time.ctime(task.get_schedule_time(since)),
                         'Sat Jul 20 10:00:00 2013')

if __name__ == '__main__':
    unittest.main()
