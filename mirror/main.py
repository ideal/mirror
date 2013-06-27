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
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#


"""Main starting point for Mirror.  Contains the main() entry point."""

import os, sys
from   optparse import OptionParser

import mirror.log
import mirror.error

def version_callback(option, opt_str, value, parser):
    print(os.path.basename(sys.argv[0]) + ": " + mirror.common.get_version())
    sys.exit(0)

def start_daemon():
    """Entry point for daemon script"""
    import mirror.common
    mirror.common.setup_translations()

    # Setup the argument parser
    parser = OptionParser(usage="%prog [options]")
    parser.add_option("-v", "--version", action="callback",
                      callback=version_callback,
                      help=_("Show program's version number and exit"))
    parser.add_option("-D", "--do-not-daemonize", dest="donot",
                      help=_("Do not daemonize (default is daemonize)"), action="store_true", default=False)
    parser.add_option("-c", "--config", dest="config",
                      help=_("Set the config location directory"), action="store", type="str")
    parser.add_option("-P", "--pidfile", dest="pidfile",
                      help=_("Use pidfile to store process id"), action="store", type="str")
    parser.add_option("-u", "--user", dest="user",
                      help=_("User to switch to. Need to start as root"), action="store", type="str")
    parser.add_option("-g", "--group", dest="group",
                      help=_("Group to switch to. Need to start as root"), action="store", type="str")
    parser.add_option("-l", "--logfile", dest="logfile",
                      help=_("Set the logfile location"), action="store", type="str")
    parser.add_option("-L", "--loglevel", dest="loglevel",
                      help=_("Set the log level: none, info, warning, error, critical, debug"), action="store", type="str")
    parser.add_option("-q", "--quiet", dest="quiet",
                      help=_("Sets the log level to 'none', this is the same as `-L none`"), action="store_true", default=False)
    parser.add_option("-r", "--rotate-logs",
                      help=_("Rotate logfiles."), action="store_true", default=False)
    parser.add_option("--profile", dest="profile", action="store_true", default=False,
                      help=_("Profiles the daemon"))

    # Get the options and args from the OptionParser
    (options, args) = parser.parse_args()

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
            print("There was an error setting the config dir! Exiting..")
            sys.exit(1)

    # Sets the options.logfile to point to the default location
    def set_logfile():
        if not options.logfile:
            options.logfile = mirror.configmanager.get_config_dir("mirrord.log")

    set_logfile()

    # Setup the logger
    try:
        # Try to make the logfile's directory if it doesn't exist
        os.makedirs(os.path.abspath(os.path.dirname(options.logfile)))
    except:
        pass

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

    # Close stdin, stdout, stderr ...
    if not options.donot:
        os.close(sys.stdin.fileno())
        os.close(sys.stdout.fileno())
        os.close(sys.stderr.fileno())

    import logging
    log = logging.getLogger(__name__)

    if options.profile:
        import hotshot
        hsp = hotshot.Profile(mirror.configmanager.get_config_dir("mirrord.profile"))
        hsp.start()
    try:
        from mirror.scheduler import Scheduler
        scheduler = Scheduler(options, args)
        scheduler.start()
    except mirror.error.MirrordRunningError, e:
        log.error(e)
        log.error("You cannot run multiple daemons with the same config directory set.")
        sys.exit(1)
    except Exception, e:
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
