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
import mirror.component as component
from mirror.pluginbase import PluginBase

log = logging.getLogger(__name__)

class Plugin(PluginBase):

    def enable(self):
        event_manager = component.get("EventManager")
        event_manager.register_event_handler("MirrorStartEvent",
                                             self.__on_mirror_start_event)
        log.info(("I am a slate fish living in the upstream river"
                  " of Qiandao Lake."))

    def disable(self):
        pass

    def __on_mirror_start_event(self):
        import time
        self.start_time = time.time()
        log.info("Hi, this is message from SlateFish: %r", self.start_time)
