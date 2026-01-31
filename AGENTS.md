# Mirror - Task Scheduler for Open Source Mirror Sites

## Project Overview

Mirror is a Python-based task scheduler application designed for open source mirror sites (e.g., mirror.bjtu.edu.cn) to synchronize files from upstream sources. It uses rsync internally and works similarly to cron but with additional features like priority-based scheduling, load balancing, and timeout handling.

**Key Features:**
- Cron-like scheduling with priority-based task execution
- System load and HTTP connection-aware scheduling
- Two-stage syncing support (for Ubuntu, Debian)
- Plugin system for extensibility
- Task timeout and auto-retry mechanisms
- Internationalization (i18n) support

**Version:** 0.8.4
**License:** GPLv3
**Python Support:** 2.7, 3.5, 3.6, 3.7, 3.8

## Project Structure

```
mirror/                     # Main source code
├── __init__.py            # Package initialization (namespace package)
├── main.py                # Entry point for daemon (mirrord)
├── daemon.py              # MirrorDaemon class - main daemon orchestration
├── scheduler.py           # Task scheduler with priority queue
├── task.py                # Task classes (Task, SimpleTask, SystemTask)
├── queue.py               # Priority queue implementation for tasks
├── component.py           # Component registry for dependency management
├── event.py               # Event definitions (MirrorEvent hierarchy)
├── eventmanager.py        # Event emission and handling
├── pluginmanager.py       # Plugin loading and management
├── pluginbase.py          # Base class for plugins
├── pluginthread.py        # Thread for plugin execution
├── config.py              # Configuration file parsing (INI format)
├── configmanager.py       # Configuration manager singleton
├── common.py              # Utility functions (version, i18n, cron parsing)
├── log.py                 # Logging setup and configuration
├── error.py               # Custom exception classes
├── handler.py             # Signal handlers (SIGTERM, SIGCHLD, SIGHUP)
├── console.py             # CLI commands (-t for task list, -s for signals)
├── sysinfo.py             # System info (load avg, TCP connections)
├── color.py               # Terminal color utilities
├── bus.py                 # D-Bus integration (optional)
├── plugins/               # Built-in plugins
│   ├── Notifier/          # Notification plugin
│   ├── SlateFish/         # Web status plugin
│   ├── SystemTask/        # System maintenance tasks
│   └── TaskStatus/        # Task status export plugin
└── i18n/                  # Internationalization files
    ├── mirror.pot         # Translation template
    └── zh_CN.po           # Chinese translation

config/                    # Configuration examples
├── mirror.ini             # Main configuration example
├── bjtu.ini               # Production config for BJTU mirror
└── plugin.ini             # Plugin configuration

test/                      # Unit tests
├── test_task.py           # Task scheduling tests
└── test_taskqueue.py      # Priority queue tests

docs/man/                  # Man page
└── mirrord.1              # Manual page for mirrord

completion/                # Shell completions
├── bash/mirrord           # Bash completion
└── zsh/_mirrord           # Zsh completion

util/systemd/              # SystemD service files
└── system/mirrord@.service
```

## Technology Stack

- **Language:** Python (2.7, 3.5+)
- **Build System:** setuptools
- **Dependencies:**
  - `setuptools` - Package management
  - `chardet` - Character encoding detection
- **Optional Dependencies:**
  - `xdg` - XDG Base Directory specification support

## Build and Installation

### Install from PyPI
```bash
sudo pip install mirror
```

### Install from Source
```bash
python setup.py build
sudo python setup.py install
```

### Build Commands
```bash
# Build translations (.po to .mo)
python setup.py build_trans

# Build plugins into .egg files
python setup.py build_plugins

# Run tests
python setup.py test

# Clean build artifacts
python setup.py clean
```

### Setup Directories
```bash
sudo mkdir -p /etc/mirror /var/log/mirrord /var/log/rsync
sudo cp config/mirror.ini /etc/mirror/
sudo chown mirror:mirror /var/log/mirrord /var/log/rsync
```

## Configuration

### Main Configuration File (`mirror.ini`)

Located at `/etc/mirror/mirror.ini` or `~/.config/mirror/mirror.ini`:

```ini
[general]
emails     = admin@example.com
loadlimit  = 2.0          # Max system load before throttling
httpconn   = 1200         # Max HTTP connections before throttling
logdir     = /var/log/rsync/
maxtasks   = 10           # Max concurrent tasks

[archlinux]
upstream[] = mirror.aarnet.edu.au
command    = rsync
exclude    = --exclude .~tmp~/
time       = * */2 * * *  # Cron-like schedule (every 2 hours)
rsyncdir   = archlinux/
localdir   = /home/mirror/archlinux
args       = --links --hard-links --times --verbose --delete --recursive
twostage   = 0            # Two-stage sync (0=disabled, 1=enabled)
timeout    = 12h          # Task timeout (0=no timeout)
priority   = 10           # 1=highest, 10=lowest
autoretry  = 1m           # Auto-retry on failure
```

### Task Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `upstream[]` | Upstream rsync server (array syntax for multiple) | Required |
| `command` | Command to execute | rsync |
| `time` | Cron-like schedule expression | Required |
| `rsyncdir` | Remote rsync module path | Required |
| `localdir` | Local destination path | Required |
| `args` | Command arguments | `--links --hard-links...` |
| `exclude` | Exclusion patterns | None |
| `twostage` | Enable two-stage sync | 0 |
| `firststage` | First stage path (if twostage=1) | None |
| `timeout` | Task timeout (seconds or XhYm) | 0 |
| `priority` | Task priority (1-10) | 10 |
| `autoretry` | Retry interval on failure | 0 |
| `type` | Task type (simple, or omit for rsync) | rsync |

### Time Format (Cron-like)
- `* */2 * * *` - Every 2 hours
- `0 2,14 * * *` - At 2:00 and 14:00
- `*/30 * * * *` - Every 30 minutes
- `0-20/2 * * * *` - Every 2 minutes from 0-20

### Time Duration Format
- `1200` - 1200 seconds
- `12h` - 12 hours
- `12h4m` - 12 hours and 4 minutes

## Running the Application

### Start Daemon
```bash
# Start as daemon (default)
mirrord

# Start in foreground (debug mode)
mirrord -D

# Start with custom config
mirrord -c /path/to/config/dir

# Start with custom log file
mirrord -l /var/log/mirrord/mirrord.log

# Start with specific user/group (after starting as root)
mirrord -u mirror -g mirror
```

### Control Commands
```bash
# List current task queue
mirrord -t

# Stop daemon
mirrord -s stop

# Reload configuration
mirrord -s reload
```

### Signal Handling
- `SIGTERM`, `SIGQUIT`, `SIGINT` - Graceful shutdown
- `SIGHUP` - Reload configuration
- `SIGCHLD` - Child process (task) finished

## Architecture

### Core Components

1. **MirrorDaemon** (`daemon.py`)
   - Main orchestrator
   - Initializes EventManager, PluginManager, Scheduler

2. **Scheduler** (`scheduler.py`)
   - Priority-based task scheduling
   - System load-aware execution decisions
   - Queue management with `TaskInfo` objects

3. **Task Types** (`task.py`)
   - `Task` - Standard rsync-based mirror task
   - `SimpleTask` - Generic command execution
   - `SystemTask` - Internal maintenance tasks

4. **Event System**
   - `MirrorEvent` - Base event class
   - `TaskStartEvent`, `TaskStopEvent`, `TaskEnqueueEvent`
   - Plugin hooks via EventManager

5. **Plugin System** (`pluginmanager.py`, `pluginbase.py`)
   - Entry point based: `mirror.plugin.mirrorplugin`
   - Plugins as setuptools eggs in `mirror/plugins/`
   - Enable/disable lifecycle hooks

### Scheduling Algorithm

1. Tasks are stored in a priority queue sorted by (time, priority)
2. Scheduler sleeps until next task's scheduled time
3. Before running, scheduler checks:
   - System load < `loadlimit`
   - HTTP connections < `httpconn`
   - Running tasks < `maxtasks` (unless priority ≤ 2)
4. If conditions not met, task is delayed by 30 minutes
5. Two-stage tasks run first stage, then immediately second stage

### Process Model

```
mirrord (main process)
├── Scheduler (main loop)
│   └── fork() → rsync tasks
├── EventManager
│   └── PluginThread (for async plugin execution)
└── Signal handlers
```

## Testing

### Run Tests
```bash
# Run all tests
python setup.py test

# Run with verbose output
python setup.py test --args="-v"
```

### Test Files
- `test/test_task.py` - Tests Task class scheduling logic
- `test/test_taskqueue.py` - Tests priority queue operations

### CI/CD
GitHub Actions workflow (`.github/workflows/mirror-test.yml`):
- Tests on Python 2.7, 3.5, 3.6, 3.7, 3.8
- Runs on Ubuntu
- Command: `python setup.py test`

## Code Style Guidelines

- **Line Length:** 127 characters (per CI config)
- **Indentation:** 4 spaces
- **Encoding:** UTF-8
- **Documentation:** Docstrings for public methods
- **Copyright:** All files include GPLv3 header

### Naming Conventions
- Classes: `CamelCase` (e.g., `MirrorDaemon`, `TaskInfo`)
- Functions/Variables: `snake_case` (e.g., `get_schedule_time`)
- Constants: `UPPER_CASE` (e.g., `PRIORITY_MIN`, `REGULAR_TASK`)
- Private: `_prefix` (e.g., `_component_registry`)

## Plugin Development

### Plugin Structure
```
mirror/plugins/MyPlugin/
├── setup.py
└── mirror/
    └── plugins/
        └── myplugin/
            ├── __init__.py
            └── myplugin.py
```

### Minimal Plugin Example
```python
# mirror/plugins/myplugin/myplugin.py
from mirror.pluginbase import PluginBase

class MyPlugin(PluginBase):
    enabled = True  # Set to False to disable
    
    def enable(self):
        # Register event handlers
        pass
    
    def disable(self):
        # Cleanup
        pass
```

### setup.py for Plugin
```python
from setuptools import setup, find_packages

setup(
    name="MyPlugin",
    version="0.1.0",
    packages=find_packages(),
    namespace_packages=["mirror", "mirror.plugins"],
    entry_points="""
    [mirror.plugin.mirrorplugin]
    MyPlugin = mirror.plugins.myplugin:MyPlugin
    """
)
```

## Security Considerations

1. **User Privileges**
   - Daemon can start as root and switch to unprivileged user via `-u` / `-g`
   - Recommended: Create dedicated `mirror` user

2. **File Permissions**
   - Log directories need write access for mirror user
   - Config directory should be readable only by mirror user

3. **Task Isolation**
   - Each task runs in separate forked process
   - Tasks cannot interfere with scheduler directly

4. **Path Validation**
   - Local directories are created if missing
   - Command paths are validated against PATH

## Debugging

### Enable Debug Logging
```bash
mirrord -D -L debug
```

### Profile Performance
```bash
mirrord --profile
# Generates mirrord.profile in config directory
```

### Check Task Queue
```bash
mirrord -t
```

### View Task Logs
```bash
# Task-specific logs
tail -f /var/log/rsync/archlinux.log.$(date +%Y-%m-%d)

# Daemon logs
tail -f /var/log/mirrord/mirrord.log
```

## Common Issues

1. **"Config dir does not exist"**
   - Create `/etc/mirror/` or `~/.config/mirror/`
   - Copy `config/mirror.ini` example

2. **"There was an error writing logs"**
   - Ensure `/var/log/mirrord/` and `/var/log/rsync/` exist
   - Check ownership: `chown mirror:mirror /var/log/mirrord /var/log/rsync`

3. **Tasks not running**
   - Check priority vs. current system load
   - Verify time format is correct
   - Check `enabled` status in config

## Authors

- Shang Yuanchun ('ideal') <idealities@gmail.com>
- Bob Gao <gaobo@bjtu.edu.cn>
- Chestnut <chestnut@bjtu.edu.cn>
