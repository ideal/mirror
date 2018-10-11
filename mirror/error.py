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

MIRROR_OK     = 0
MIRROR_ERROR  = 1
MIRROR_ERRARG = 2

class MirrorError(Exception):
    def __new__(cls, *args, **kwargs):
        inst = super(MirrorError, cls).__new__(cls, *args, **kwargs)
        inst._args = args
        inst._kwargs = kwargs
        return inst

    def __init__(self, *args, **kwargs):
        if len(args) == 0:
            self._message = ""
        elif len(args) == 1:
            self._message = args[0]
        else:
            self._message = args[0] % args[1:]

    def _set_message(self, message):
        self._message = message

    def _get_message(self):
        return self._message

    message = property(_get_message, _set_message)

    del _get_message, _set_message

    def __str__(self):
        return self.message

class MirrordRunningError(MirrorError):
    pass

class MirrordTaskFinishedFakeError(MirrorError):
    pass

