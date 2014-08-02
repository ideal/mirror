#
# Copyright (C) 2014 Shang Yuanchun <idealities@gmail.com>
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

import sys
import unittest
from os import listdir
from os.path import dirname

def test_suite():
    # Build the list of modules
    modules = []
    for name in listdir(dirname(__file__)):
        if not name.startswith('test_'):
            continue
        if not name.endswith('.py'):
            continue
        module = 'test.%s' % name[:-3]
        # Check the module imports correctly, have a nice error otherwise
        __import__(module)
        modules.append(module)

    return unittest.defaultTestLoader.loadTestsFromNames(modules)

if __name__ == '__main__':
    sys.path.insert(0, '')
    unittest.main(module=__name__, defaultTest='test_suite', argv=sys.argv[:1])

