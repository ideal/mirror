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
from mirror.component import Component

log = logging.getLogger(__name__)

class PluginBase(Component):

    def __init__(self, name):
        super(PluginBase, self).__init__(name)
        self.name = name
        log.debug("Plugin %s initialized...", self.name)

    def enable(self):
        raise NotImplementedError("Need to define an enable method!")

    def disable(self):
        raise NotImplementedError("Need to define a disable method!")

