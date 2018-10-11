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

"""Logging functions"""

import logging

from mirror import common

__all__ = ["setupLogger", "setLoggerLevel", "addStreamHandler"]

if 'dev' in common.get_version():
    DEFAULT_LOGGING_FORMAT = "%%(asctime)s.%%(msecs)03.0f [%%(levelname)-8s]"\
                             "[%%(name)-%ds:%%(lineno)-4d] %%(message)s"
else:
    DEFAULT_LOGGING_FORMAT = "%%(asctime)s [%%(levelname)-8s][%%(name)-%ds] %%(message)s"

MAX_LOGGER_NAME_LENGTH = 16

levels = {
    "none":     logging.NOTSET,
    "info":     logging.INFO,
    "warn":     logging.WARNING,
    "warning":  logging.WARNING,
    "error":    logging.ERROR,
    "critical": logging.CRITICAL,
    "debug":    logging.DEBUG,
    "trace":    5,
    "garbage":  1
}

def setupLogger(level="error", filename=None, filemode="w"):
    """
    Sets up the basic logger and if `:param:filename` is set, then it will log
    to that file instead of stdout.

    :param level: str, the level to log
    :param filename: str, the file to log to
    """
    import logging
    logging.setLoggerClass(logging.Logger)
    logging.addLevelName(5, 'TRACE')
    logging.addLevelName(1, 'GARBAGE')

    level = levels.get(level, logging.ERROR)

    rootLogger = logging.getLogger()

    if filename and filemode=='a':
        import logging.handlers
        handler = logging.handlers.RotatingFileHandler(
            filename, filemode,
            maxBytes=50*1024*1024,   # 50 Mb
            backupCount=8,
            encoding='utf-8',
            delay=0
        )
    elif filename and filemode=='w':
        import logging.handlers
        handler = getattr(
            logging.handlers, 'WatchedFileHandler', logging.FileHandler)(
                filename, filemode, 'utf-8', delay=0
        )
    else:
        handler = logging.StreamHandler()

    handler.setLevel(level)

    formatter = logging.Formatter(
        DEFAULT_LOGGING_FORMAT % MAX_LOGGER_NAME_LENGTH,
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler.setFormatter(formatter)

    rootLogger.addHandler(handler)
    rootLogger.setLevel(level)

def setLoggerLevel(level, logger_name=None):
    """
    Sets the logger level.

    :param level: str, a string representing the desired level
    :param logger_name: str, a string representing desired logger name for which
                        the level should change. The default is "None" will will
                        tweak the root logger level.

    """
    logging.getLogger(logger_name).setLevel(levels.get(level, logging.ERROR))

def addStreamHandler(level="error", force=False):
    """
    Add a stream handler to logger. If there is already one and force is not set, the addition is canceled.

    :param level: str, a string representing the desired level
    :param force: bool, whether to add when there is already one

    """
    if not force:
        for handler in logging.getLogger().handlers:
            if handler.__class__ == logging.StreamHandler:
                return

    level = levels.get(level, logging.ERROR)

    handler = logging.StreamHandler()
    handler.setLevel(level)

    formatter = logging.Formatter(
        DEFAULT_LOGGING_FORMAT % MAX_LOGGER_NAME_LENGTH,
        datefmt="%m-%d %H:%M:%S"
    )

    handler.setFormatter(formatter)

    logging.getLogger().addHandler(handler)
