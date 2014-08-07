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


import logging
import mirror.component   as     component
from mirror.scheduler     import Scheduler
from mirror.eventmanager  import EventManager
from mirror.pluginmanager import PluginManager

log = logging.getLogger(__name__)

class MirrorDaemon(object):

    def __init__(self, options = None, args = None):
        self.event_manager  = EventManager()
        self.plugin_manager = PluginManager("plugin.ini", "mirror.plugin.mirrorplugin")
        component.start()

        self.scheduler = Scheduler(options, args)

    def start(self):
        log.info("Starting mirror scheduler...")
        self.scheduler.start()

