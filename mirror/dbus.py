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

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

class MirrorBus(dbus.service.Object):
    def __init__(self, scheduler):
        self.scheduler = scheduler

        busname = dbus.service.BusName("cn.edu.bjtu.mirror", bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, busname, "/cn/edu/bjtu/mirror")

    @dbus.service.method("cn.edu.bjtu.mirror")
    def list_queue(self):
        print("queue")

    @classmethod
    def start(self):
        DBusGMainLoop(set_as_default=True)
