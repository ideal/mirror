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

from mirror.sysinfo import enum

FOREGROUND_COLORS = enum(
                    BLACK  = '\033[30m',
                    RED    = '\033[31m',
                    GREEN  = '\033[32m',
                    YELLOW = '\033[33m',
                    BLUE   = '\033[34m',
                    MAGENTA= '\033[35m',
                    CYAN   = '\033[36m',
                    WHITE  = '\033[37m',
                    )

BACKGROUND_COLORS = enum(
                    BLACK  = '\033[40m',
                    RED    = '\033[41m',
                    GREEN  = '\033[42m',
                    YELLOW = '\033[43m',
                    BLUE   = '\033[44m',
                    MAGENTA= '\033[45m',
                    CYAN   = '\033[46m',
                    WHITE  = '\033[47m',
                    )

COLOR_RESET = '\033[0m'
