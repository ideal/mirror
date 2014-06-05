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


import time
import logging
import threading
import mirror.component as component

log = logging.getLogger("pluginthread")

class PluginThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self, name="mirror.plugin")
        # python list is thread safe
        self.event_queue   = [ ]
        self.event_manager = component.get("EventManager")
        self.stop_event    = threading.Event()

    def add_event(self, event):
        self.event_queue.append(event)

    def run(self):
        log.debug("Plugin thread started")
        sleep_count = 0
        while (True):
            if self.stop_event.isSet() and len(self.event_queue) == 0:
                log.debug("PluginThread's stop_event is set, thread is exiting...")
                break
            try:
                event = self.event_queue.pop(0)
            except:
                time.sleep(0.1)
                sleep_count += 1
                if sleep_count > 600:
                    log.debug("Plugin thread finished")
                    break
                else:
                    continue
            # Call any handlers for the event
            for handler in self.event_manager.handlers[event.name]:
                log.debug("Running handler %s for event %s with args: %s",
                          event.name, handler, event.args)
                try:
                    handler(*event.args)
                except Exception as e:
                    log.error("Event handler %s failed in %s with exception: %s",
                              event.name, handler, e)

