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


import os
import re
import socket

d = { 1: 0, 5: 1, 15: 2}

def loadavg(duration = 5):
    if duration not in d:
        duration = 5
    if hasattr(os, "getloadavg"):
        return os.getloadavg()[d[duration]]
    try:
        loadavgs = open("/proc/loadavg").read().split(" ")
        return float(loadavgs[d[duration]])
    except:
        return 0.0

def enum(**enums):
    return type('Enum', (), enums)

# st in enum in /usr/include/netinet/tcp.h
TCP_STATUS = enum(TCP_ESTABLISHED =1,\
                  TCP_SYN_SENT    =2,\
                  TCP_SYN_RECV    =3,\
                  TCP_FIN_WAIT1   =4,\
                  TCP_FIN_WAIT2   =5,\
                  TCP_TIME_WAIT   =6,\
                  TCP_CLOSE       =7,\
                  TCP_CLOSE_WAIT  =8,\
                  TCP_LAST_ACK    =9,\
                  TCP_LISTEN      =10,\
                  TCP_CLOSING     =11)

pattern = (r"\d+:\s+" + 
           r"(?P<local_addr>[\da-fA-F]+):(?P<local_port>[\da-fA-F]+)\s+" +
           r"(?P<remote_addr>[\da-fA-F]+):(?P<remote_port>[\da-fA-F]+)\s+" +
           r"(?P<status>[\da-fA-F]+)\s+[\da-fA-F]+:[\da-fA-F]+\s+[\da-fA-F]+:[\da-fA-F]+\s+[\da-fA-F]+\s+\d+\s+\d+\s+" +
           r"(?P<inode>\d+)")

def tcpconn(port = 80):
    try:
        # TODO: using AF_NETLINK to fetch tcp information instead from /proc
        sock = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW)
        sock.close()
    except Exception as e:
        pass
    connections = 0
    tcp   = re.compile(pattern)
    files = ("/proc/net/tcp", "/proc/net/tcp6")
    for path in files:
        if os.access(path, os.R_OK):
            fp = open(path)
            fp.readline() # skip title
            for line in fp:
                conn = tcp.search(line).groupdict()
                local_port = int(conn['local_port'], 16)
                if local_port != port:
                    continue
                status = int(conn['status'], 16)
                if status == TCP_STATUS.TCP_ESTABLISHED:
                    connections += 1
            fp.close()
    return connections

if __name__ == "__main__":
    print("Current connections: %d" % tcpconn(port = 44971))
