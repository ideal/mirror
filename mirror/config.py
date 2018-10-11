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
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#

import logging
import shutil
import os

import sys
if sys.version_info.major >= 3:
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser

import mirror.common

log = logging.getLogger(__name__)

def prop(func):
    """Function decorator for defining property attributes

    The decorated function is expected to return a dictionary
    containing one or more of the following pairs:
        fget - function for getting attribute value
        fset - function for setting attribute value
        fdel - function for deleting attribute
    This can be conveniently constructed by the locals() builtin
    function; see:
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/205183
    """
    return property(doc=func.__doc__, **func())

class Config(object):
    def __init__(self, filename, defaults=None, config_dir=None):
        self.__config           = {}
        self.__set_functions    = {}
        self.__change_callbacks = []

        if defaults:
            for key, value in defaults.items():
                self.set_item(key, value)

        # Load the config from file in the config_dir
        if config_dir:
            self.__config_file = os.path.join(config_dir, filename)
        else:
            self.__config_file = mirror.common.get_default_config_dir(filename)

        self.load()

    def __iter__(self):
        for key in self.__config:
            yield key

    def __contains__(self, item):
        return item in self.__config

    def __setitem__(self, key, value):
        return self.set_item(key, value)

    def set_item(self, key, value):
        """
        **Usage**

        >>> config = Config("mirror.ini")
        >>> config["archlinux"] = {"upstream": "archlinux.org"}
        >>> config["archlinux"]
        {"upstream": "archlinux.org"}

        """
        value = mirror.common.utf8_encoded(value)

        if key not in self.__config:
            self.__config[key] = value
            log.debug("Setting '%s' to %s with type %s", key, value, type(value))
            return

        if self.__config[key] == value:
            return

        # Do not allow the type to change unless it is None
        oldtype, newtype = type(self.__config[key]), type(value)

        if value is not None and oldtype != type(None) and oldtype != newtype:
            try:
                if oldtype == unicode:
                    value = oldtype(value, "utf8")
                else:
                    value = oldtype(value)
            except ValueError:
                log.warning("Type '%s' invalid for '%s'", newtype, key)
                raise

        log.debug("Setting '%s' to %s with type %s", key, value, type(value))

        self.__config[key] = value

        # call set functions
        try:
            for func in self.__set_functions[key]:
                func(key, value)
        except KeyError:
            pass
        # call change callbacks
        try:
            for func in self.__change_callbacks:
                func(key, value)
        except:
            pass

    def __getitem__(self, key):
        return self.get_item(key)

    def get_item(self, key):
        """
        **Usage**

        >>> config = Config("mirror.ini")
        >>> config["archlinux"]
        {"upstream": "archlinux.org"}

        """
        if isinstance(self.__config[key], str):
            try:
                return self.__config[key].decode("utf8")
            except UnicodeDecodeError:
                return self.__config[key]
        else:
            return self.__config[key]

    def __delitem__(self, key):
        """
        See
        :meth:`del_item`
        """
        self.del_item(key)

    def del_item(self, key):
        """
        Deletes item with a specific key from the configuration.

        **Usage**
        >>> config = Config("mirror.ini")
        >>> del config["archlinux"]
        """
        del self.__config[key]

    def register_change_callback(self, callback):
        """
        **Usage**

        >>> config = Config("mirror.ini", defaults={"test": 5})
        >>> def callback(key, value):
        ...     print(key, value)
        ...
        >>> config.register_change_callback(callback)

        """
        self.__change_callbacks.append(callback)

    def register_set_function(self, key, function, apply_now=True):
        """
        Register a function to be called when a config value changes

        **Usage**

        >>> config = Config("mirror.ini", defaults={"test": 5})
        >>> def callback(key, value):
        ...     print(key, value)
        ...
        >>> config.register_set_function("test", callback, apply_now=True)
        test 5

        """
        log.debug("Registering function for %s key..", key)
        if key not in self.__set_functions:
            self.__set_functions[key] = []

        self.__set_functions[key].append(function)

        # Run the function now if apply_now is set
        if apply_now:
            function(key, self.__config[key])
        return

    def apply_all(self):
        """
        Calls all set functions

        **Usage**

        >>> config = Config("mirror.ini", defaults={"test": 5})
        >>> def callbck(key, value):
        ...     print(key, value)
        ...
        >>> config.register_set_function("test", callback, apply_now=False)
        >>> config.apply_all()
        test 5

        """
        log.debug("Calling all set functions..")
        for key, value in self.__set_functions.items():
            for func in value:
                func(key, self.__config[key])

    def apply_set_functions(self, key):
        """
        Calls set functions for `:param:key`.

        """
        log.debug("Calling set functions for key %s..", key)
        if key in self.__set_functions:
            for func in self.__set_functions[key]:
                func(key, self.__config[key])

    def load(self, filename=None):
        """
        Load a config file

        """
        if not filename:
            filename = self.__config_file

        try:
            data = open(filename, "rb").read()
        except IOError as e:
            log.warning("Unable to open config file %s: %s", filename, e)
            return

        # load mirror ini config file
        config = ConfigParser()
        config.read(filename)
        for section in config.sections():
            value = {}
            for item in config.items(section):
                if item[0].endswith("[]") and item[0] not in value:
                    value[item[0]] = [item[1]]
                    continue
                if item[0] in value and type(value[item[0]]) == list:
                    value[item[0]].append(item[1])
                else:
                    value[item[0]] = item[1]
            self.set_item(section, value)

    def save(self, filename=None):
        """
        Save configuration to disk

        """
        if not filename:
            filename = self.__config_file

        # Save the new config and make sure it's written to disk
        try:
            log.debug("Saving new config file %s", filename + ".new")
            f = open(filename + ".new", "w")
            # TODO: save ini config
            for section, value in self.__config.items():
                f.write("[" + section + "]\n")
                for key, val in value.items():
                    if key.endswith("[]"):
                        for v in val:
                            f.write(key + "\t=\t" + v + "\n")
                    else:
                        f.write(key + "\t=\t" + val + "\n")
                f.write("\n")
            f.flush()
            os.fsync(f.fileno())
            f.close()
        except IOError as e:
            log.error("Error writing new config file: %s", e)
            return False

        # Make a backup of the old config
        try:
            log.debug("Backing up old config file to %s~", filename)
            shutil.move(filename, filename + "~")
        except Exception as e:
            log.warning("Unable to backup old config...")

        # The new config file has been written successfully, so let's move it over
        # the existing one.
        try:
            log.debug("Moving new config file %s to %s..", filename + ".new", filename)
            shutil.move(filename + ".new", filename)
        except Exception as e:
            log.error("Error moving new config file: %s", e)
            return False
        else:
            return True

    @property
    def config_file(self):
        return self.__config_file

    @prop
    def config():
        """The config dictionary"""
        def fget(self):
            return self.__config
        def fdel(self):
            return self.save()
        return locals()
