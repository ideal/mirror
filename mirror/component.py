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
from collections import defaultdict

log = logging.getLogger(__name__)

class Component(object):

    def __init__(self, name, depend = None):
        self._name   = name
        self._depend = depend
        _component_registry.register(self)

    def start(self):
        pass

    def stop(self):
        pass

class ComponentRegistry(object):

    def __init__(self):
        self.components = {}
        # Stores all of the components that are dependent on a
        # particular component
        self.dependents = defaultdict(list)

    def register(self, obj):
        """
        Register a component object with the registry.  This is done
        automatically when a Component object is instantiated.

        :param obj: the Component object

        :raises ComponentAlreadyRegistered: if a component with the
        same name is already registered.

        """
        name = obj._name

        if not isinstance(obj, Component):
            log.warn("Trying to register a object with type: %s",
                         obj.__class__.__name__)
            return

        if name in self.components:
            log.warn(("Trying to register a object which is already"
                         " registered, name: %s"), 
                         name)

        self.components[obj._name] = obj

        if obj._depend:
            for depend in obj._depend:
                self.dependents[depend].append(name)

    def deregister(self, obj):
        """
        Deregisters a component from the registry.

        :param obj: the Component object

        """

        if obj in self.components.values():
            log.debug("Deregistering Component: %s", obj._name)
            self.stop([obj._name])
            self.components.pop(obj._name)

    def start(self, names = []):
        """
        Starts Components that are currently in a Stopped state and their
        dependencies.  If *names* is specified, will only start those
        Components and their dependencies and if not it will start all
        registered components.

        :param names: a list of Components to start

        """
        # Start all the components if names is empty
        if not names:
            names = list(self.components)
        elif isinstance(names, str):
            names = [ names ]

        for name in names:
            if self.components[name]._depend:
                # This component has depends, so we need to start them first.
                self.start(self.components[name]._depend)
            log.debug("Starting component: %s", name)
            self.components[name].start()

    def stop(self, names = []):
        """
        Stops Components that are currently not in a Stopped state.  If
        *names* is specified, then it will only stop those Components,
        and if not it will stop all the registered Components.

        :param names: a list of Components to stop

        """
        if not names:
            names = list(self.components)
        elif isinstance(names, str):
            names = [ names ]

        stopped = set()

        for name in names:
            if name in stopped:
                continue
            if name not in self.components:
                continue
            if name in self.dependents:
                # If other components depend on this component, stop them first
                self.stop(self.dependents[name])
                stopped.update(self.dependents[name])
            self.components[name].stop()

_component_registry = ComponentRegistry()

# methods provided by mirror.component

def get(name):
    """
    Return a reference to a component.

    :param name: the Component name to get

    :returns: the Component object, or None
    if the Component does not exist

    """
    return _component_registry.components.get(name, None)

deregister = _component_registry.deregister
start      = _component_registry.start
stop       = _component_registry.stop

