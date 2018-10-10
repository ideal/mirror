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

import bisect

class TaskInfo():
    def __init__(self, name, tasktype, time, priority):
        self.name     = name
        self.tasktype = tasktype
        self.time     = time
        self.priority = priority

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return (self.time - other.time < 0) if self.time != other.time else (
                                           self.priority - other.priority < 0)

    def __cmp__(self, other):
        return (self.time - other.time) if self.time != other.time else (
                                           self.priority - other.priority)

    def __str__(self):
        return "(name: %s, type: %d, time: %d, priority: %d)" % (self.name,
                                    self.tasktype, self.time, self.priority)

class Queue(object):
    def __init__(self, *items):
        self.queue = []
        for item in items:
            if not isinstance(item, TaskInfo):
                continue
            self.put(item)

    def put(self, item):
        bisect.insort(self.queue, item)

    def get(self):
        try:
            return self.queue.pop(0)
        except:
            return None

    def remove(self, item):
        self.queue.remove(item)

    def empty(self):
        return ( len(self.queue) == 0 )

    def size(self, key = None, value = None):
        if key is None or value is None:
            return len(self.queue)
        else:
            if self.empty():
                return 0
            if not hasattr(self.queue[0], key):
                return 0
            count = 0
            for item in self.queue:
                count += ( getattr(item, key) == value )
            return count

    def find(self, name):
        for taskinfo in self.queue:
            if taskinfo.name == name:
                return taskinfo
        return None

    def __getitem__(self, key):
        try:
            return self.queue[key]
        except:
            return None

    def __str__(self):
        return "[" + ",".join([str(item) for item in self.queue]) + "]"

    def __iter__(self):
        for item in self.queue:
            yield item

    def __contains__(self, item):
        return item in self.queue

if __name__ == "__main__":
    task1 = TaskInfo("Buy clock",    0, 1376712000, 2)
    task2 = TaskInfo("Basketball",   0, 1376701200, 1)
    task3 = TaskInfo("Wash clothes", 0, 1376701200, 2)
    task4 = TaskInfo("Send letter",  0, 1376704800, 4)

    queue = Queue(task1, task2, task3, task4, "Qiandao Lake")
    assert(queue.size() == 4)
    assert(not queue.empty())
    print(queue)

    task  = queue[0]
    print(task)

    print(task in queue)
    task4 = TaskInfo("Send letter",  0, 1376704800, 4)
    print(task4 in queue)

    print(queue.size("tasktype", 0))

