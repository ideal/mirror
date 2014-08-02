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

from mirror.queue import TaskInfo
from mirror.queue import Queue

class TaskQueueTestCase(unittest.TestCase):

    def test_taskqueue(self):
        task1 = TaskInfo("Buy clock",    0, 1376712000, 2)
        task2 = TaskInfo("Basketball",   0, 1376701200, 1)
        task3 = TaskInfo("Wash clothes", 0, 1376701200, 2)
        task4 = TaskInfo("Send letter",  0, 1376704800, 4)

        queue = Queue(task1, task2, task3, task4, "Qiandao Lake")
        self.assertEqual(queue.size(), 4)
        self.assertEqual(queue.empty(), False)

        # it is Basketball
        task  = queue[0]
        self.assertEqual(task.name, "Basketball")
        self.assertEqual(task.time, 1376701200)

if __name__ == '__main__':
    unittest.main()
