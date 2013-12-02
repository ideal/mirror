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

events = {}

class MirrorEventMetaClass(type):
    """
    The metaclass keeps a list of all known event classes.

    """
    def __init__(cls, name, bases, dct):
        super(MirrorEventMetaClass, cls).__init__(name, bases, dct)
        if name != "MirrorEvent":
            events[name] = cls

class MirrorEvent(object):
    """
    The base class for all events.

    """
    # MirrorEventMetaClass is used to generate this class
    __metaclass__ = MirrorEventMetaClass

    def _get_name(self):
        return self.__class__.__name__

    def _get_args(self):
        if hasattr(self, "_args"):
            return self._args
        return []

    name = property(fget=_get_name)
    args = property(fget=_get_args)

class MirrorStartEvent(MirrorEvent):
    """
    The event occurs when mirror daemon is to be running.

    """
    pass

class TaskEnqueueEvent(MirrorEvent):
    """
    The event occurs when a task is appended into the queue.

    :param taskname: task's name

    """
    def __init__(self, taskname):
        self._args = [ taskname ]

class PreTaskStartEvent(MirrorEvent):
    """
    The event occurs when a new task is going to be running.

    :param taskname: task's name

    """
    def __init__(self, taskname):
        self._args = [ taskname ]

class TaskStartEvent(MirrorEvent):
    """
    The event occurs when a new task is running.

    :param taskname: task's name
    :param taskpid: task's process id

    """
    def __init__(self, taskname, taskpid):
        self._args = [ taskname, taskpid ]

class TaskStopEvent(MirrorEvent):
    """
    The event occurs when a task is ended.

    :param taskname: task's name
    :param taskpid: task's process id
    :param exitcode: task's exit code

    """
    def __init__(self, taskname, taskpid, exitcode):
        self._args = [ taskname, taskpid, exitcode ]

class RunSystemTaskEvent(MirrorEvent):
    """
    The event occurs when an internal task needs to run.

    :param taskinfo: TaskInfo instance

    """
    def __init__(self, taskinfo):
        self._args = [ taskinfo ]

