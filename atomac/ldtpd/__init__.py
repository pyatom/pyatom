# Copyright (c) 2012 VMware, Inc. All Rights Reserved.

# This file is part of ATOMac.

# ATOMac is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation version 2 and no later version.

# ATOMac is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License version 2
# for more details.

# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# St, Fifth Floor, Boston, MA 02110-1301 USA.
"""Main routines for LDTP daemon.

    The LDTP daemon listens on a socket for incoming connections. These
    connections send XMLRPC commands to do perform various GUI automation
    tasks. It's the server part of a client/server UI automation architecture.
"""

import os
import sys
import core
import time
import signal
import socket
import thread
import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)
    encode_threshold = None

class LDTPServer(SimpleXMLRPCServer.SimpleXMLRPCServer):
   '''Class to override some behavior in SimpleXMLRPCServer'''
   def server_bind(self, *args, **kwargs):
       '''Server Bind. Forces reuse of port.'''
       self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
       # Can't use super() here since SimpleXMLRPCServer is an old-style class
       SimpleXMLRPCServer.SimpleXMLRPCServer.server_bind(self, *args, **kwargs)

def notifyclient(parentpid):
    time.sleep(1)
    os.kill(int(parentpid), signal.SIGUSR1)

def main(port = 4118, parentpid=None):
    """Main entry point. Parse command line options and start up a server."""
    server = LDTPServer(('', port), allow_none=True, logRequests=False,
                        requestHandler=RequestHandler)
    server.register_introspection_functions()
    server.register_multicall_functions()
    ldtp_inst = core.Core()
    server.register_instance(ldtp_inst)
    if parentpid:
        thread.start_new_thread(notifyclient, (parentpid,))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
