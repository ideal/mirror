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
from   mirror.component import Component

log = logging.getLogger(__name__)

class EventManager(Component):

    def __init__(self):
        # The name is "EventManager"
        super(Component, self).__init__(self.__class__.__name__)

        self.handlers = {}

    def emit(self, event):
        """
        Emits the event to interested clients.

        :param event: MirrorEvent
        """
        if event.name not in self.handlers:
            return
        # Call any handlers for the event
        for handler in self.handlers[event.name]:
            log.debug("Running handler %s for event %s with args: %s", event.name, handler, event.args)
            try:
                handler(*event.args)
            except Exception, e:
                log.error("Event handler %s failed in %s with exception %s", event.name, handler, e)

    def register_event_handler(self, event, handler):
        """
        Register a function to be called when a `:param:event` is emitted.

        :param event: string, the event name
        :param handler: function, to be called when `:param:event` is emitted

        """
        if event not in self.handlers:
            self.handlers[event] = []

        if handler not in self.handlers[event]:
            self.handlers[event].append(handler)

    def deregister_event_handler(self, event, handler):
        """
        Deregisters an event handler function.

        :param event: string, the event name
        :param handler: function, currently registered to handle `:param:event`

        """
        if event in self.handlers and handler in self.handlers[event]:
            self.handlers[event].remove(handler)
