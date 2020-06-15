#
# Copyright (C) 2013-2014 Shang Yuanchun <idealities@gmail.com>
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


"""Main starting point for Mirror.  Contains the main() entry point."""

import os, sys
import signal
from   optparse import OptionParser

import mirror.log
import mirror.error
import mirror.console
from mirror.common import write_stderr

def version_callback(option, opt_str, value, parser):
    print(os.path.basename(sys.argv[0]) + ": " + mirror.common.get_version())
    sys.exit(0)

def start_daemon():
    """Entry point for daemon script"""
    import mirror.common
    mirror.common.setup_translations()

    # Fix ?? problem if redirect `mirrord -h` to file or pipe to other command
    if not sys.stdout.isatty() and not mirror.common.is_python3():
        reload(sys)
        sys.setdefaultencoding('utf-8')

    # Setup the argument parser
    parser = OptionParser(usage="%prog [options]")
    parser.add_option("-v", "--version", action="callback",
                      callback=version_callback,
                      help=_("Show program's version number and exit"))
    parser.add_option("-D", "--do-not-daemonize", dest="donot",
                      help=_("Do not daemonize (default is daemonize)"),
                      action="store_true",
                      default=False)
    parser.add_option("-c", "--config", dest="config",
                      help=_("Set the config location directory"),
                      action="store", type="str")
    parser.add_option("-P", "--pidfile", dest="pidfile",
                      help=_("Use pidfile to store process id"),
                      action="store", type="str")
    parser.add_option("-u", "--user", dest="user",
                      help=_("User to switch to. Need to start as root"),
                      action="store", type="str")
    parser.add_option("-g", "--group", dest="group",
                      help=_("Group to switch to. Need to start as root"),
                      action="store", type="str")
    parser.add_option("-l", "--logfile", dest="logfile",
                      help=_("Set the logfile location"),
                      action="store", type="str")
    parser.add_option("-L", "--loglevel", dest="loglevel",
                      help=_("Set the log level: none, info, warning, error, "
                             "critical, debug"),
                      action="store", type="str")
    parser.add_option("-q", "--quiet", dest="quiet",
                      help=_("Sets the log level to 'none', this is the same as `-L none`"),
                      action="store_true", default=False)
    parser.add_option("-r", "--rotate-logs", dest="rotate_logs",
                      help=_("Rotate logfiles."),
                      action="store_true", default=False)
    parser.add_option("--profile", dest="profile",
                      help=_("Profiles the daemon"),
                      action="store_true", default=False)
    parser.add_option("-t", "--tasks", dest="list_tasks",
                      help=_("List current tasks in scheduler's queue"),
                      action="store_true", default=False)
    parser.add_option("-s", "--signal", dest="signal",
                      help=_("Send signal to mirrord: stop, reload"),
                      action="store", type="str")

    # Get the options and args from the OptionParser
    (options, args) = parser.parse_args()

    if options.list_tasks:
        sys.exit(mirror.console.list_task_queue())

    if options.signal:
        sys.exit(mirror.console.signal_process(options.signal))

    if options.quiet:
        options.loglevel = "none"
    if not options.loglevel:
        options.loglevel = "info"

    logfile_mode = 'w'
    if options.rotate_logs:
        logfile_mode = 'a'

    import mirror.configmanager
    if options.config:
        if not mirror.configmanager.set_config_dir(options.config):
            write_stderr("There was an error setting the config dir! Exiting.."),
            sys.exit(1)

    # Check if config dir exists
    config_dir = mirror.configmanager.get_config_dir()
    if not os.path.isdir(config_dir):
        write_stderr(_("Config dir does not exist: %s, please create and write your mirror.ini"),
                     config_dir)
        sys.exit(1)

    # Check if main config file exists
    config_file = mirror.configmanager.get_config_dir('mirror.ini')
    if not os.path.isfile(config_file):
        write_stderr(_("Config file does not exist: %s, please write one"),
                     config_file)
        sys.exit(1)

    # Sets the options.logfile to point to the default location
    def set_logfile():
        if not options.logfile:
            options.logfile = os.path.join(mirror.common.DEFAULT_MIRRORD_LOG_DIR,
                                           "mirrord.log")

    set_logfile()

    # Setup the logger
    try:
        log_dir = os.path.abspath(os.path.dirname(options.logfile))
        # Try to make the logfile's directory if it doesn't exist
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
    except:
        write_stderr(_("There was an error creating log dir: %s, you can create it manually and start again."),
                     log_dir)
        sys.exit(1)

    if not os.access(log_dir, os.W_OK):
        write_stderr(_("There was an error writing logs to log dir: %s, "
                       "you can change it manually (chown or chmod ) and start again."),
                     log_dir)
        sys.exit(1)

    task_log_dir = mirror.common.DEFAULT_TASK_LOG_DIR
    if not os.path.isdir(task_log_dir):
        write_stderr(_("Default task log dir does not exists: %s, you can create it manually and start again."),
                     task_log_dir)
        sys.exit(1)

    if not os.access(task_log_dir, os.W_OK):
        write_stderr(_("There was an error writing logs to log dir: %s, "
                       "you can change it manually (chown or chmod) and start again."),
                     task_log_dir)
        sys.exit(1)

    # Setup the logger
    if os.path.isfile(options.logfile):
        logfile_mode = 'a'
    mirror.log.setupLogger(level=options.loglevel,
                           filename=options.logfile,
                           filemode=logfile_mode)
    if options.donot:
        mirror.log.addStreamHandler(level=options.loglevel)

    # Writes out a pidfile if necessary
    def write_pidfile():
        if options.pidfile:
            open(options.pidfile, "wb").write("%s\n" % os.getpid())

    # If the do not daemonize is set, then we just skip the forking
    if not options.donot:
        if os.fork():
            # We've forked and this is now the parent process, so die!
            os._exit(0)
        os.setsid()
        # Do second fork
        if os.fork():
            os._exit(0)

    # Change to root directory
    os.chdir("/")
    # Write pid file before change gid and uid
    write_pidfile()

    if options.group:
        if not options.group.isdigit():
            import grp
            options.group = grp.getgrnam(options.group)[2]
        os.setgid(options.group)
    if options.user:
        if not options.user.isdigit():
            import pwd
            options.user = pwd.getpwnam(options.user)[2]
        os.setuid(options.user)

    # Redirect stdin, stdout, stderr to /dev/null ...
    # if mirrord is running as daemon
    if not options.donot:
        fp = open("/dev/null", 'r+')
        os.dup2(fp.fileno(), sys.stdin.fileno())
        os.dup2(fp.fileno(), sys.stdout.fileno())
        os.dup2(fp.fileno(), sys.stderr.fileno())
        fp.close()

    import logging
    log = logging.getLogger(__name__)

    try:
        mirror.common.check_mirrord_running(
            mirror.configmanager.get_config_dir("mirrord.pid"))
        # return fp to keep file not closed (by __exit__()), so the lock will not get released
        # we also write pid into it
        fp = mirror.common.lock_file(
            mirror.configmanager.get_config_dir("mirrord.pid"))
    except mirror.error.MirrordRunningError as e:
        log.error(e)
        log.error("You cannot run multiple daemons with the same config directory set.")
        sys.exit(1)
    except Exception as e:
        log.exception(e)
        sys.exit(1)

    import mirror.handler
    signal.signal(signal.SIGTERM, mirror.handler.shutdown_handler)
    signal.signal(signal.SIGQUIT, mirror.handler.shutdown_handler)
    signal.signal(signal.SIGINT,  mirror.handler.shutdown_handler)
    signal.signal(signal.SIGCHLD, mirror.handler.sigchld_handler)
    signal.signal(signal.SIGHUP,  mirror.handler.reload_handler)

    if options.profile:
        import hotshot
        hsp = hotshot.Profile(mirror.configmanager.get_config_dir("mirrord.profile"))
        hsp.start()
    try:
        log.info("Starting mirror daemon...")
        from mirror.daemon import MirrorDaemon
        daemon = MirrorDaemon(options, args)
        daemon.start()
    except Exception as e:
        log.exception(e)
        sys.exit(1)
    finally:
        if options.profile:
            hsp.stop()
            hsp.close()
            import hotshot.stats
            stats = hotshot.stats.load(mirror.configmanager.get_config_dir("mirrord.profile"))
            stats.strip_dirs()
            stats.sort_stats("time", "calls")
            stats.print_stats(400)
