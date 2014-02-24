# Copyright (c) 2013 Nagappan Alagappan All Rights Reserved.

# This file is part of ATOMac.

#@author: Nagappan Alagappan <nagappan@gmail.com>                                                                                                      
#@copyright: Copyright (c) 2009-13 Nagappan Alagappan                                                                                                  

#http://ldtp.freedesktop.org                                                                                                                           

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
"""Main routines for LDTP"""

import os
import re
import sys
import time
import state
import types
import atexit
import signal
import socket
import thread
import logging
import datetime
import platform
import tempfile
import warnings
import traceback
import xmlrpclib
import subprocess
from log import logger
from base64 import b64decode
from fnmatch import translate as glob_trans
from socket import error as SocketError
from client_exception import LdtpExecutionError, ERROR_CODE

LDTP_LOG_MEMINFO = 60
LDTP_LOG_CPUINFO = 61
logging.addLevelName(LDTP_LOG_MEMINFO, 'MEMINFO')
logging.addLevelName(LDTP_LOG_CPUINFO, 'CPUINFO')

_python26 = False
if sys.version_info[:2] <= (2, 6):
    _python26 = True
_ldtp_windows_env = False
if 'LDTP_DEBUG' in os.environ:
    _ldtp_debug = os.environ['LDTP_DEBUG']
else:
    _ldtp_debug = None
if 'LDTP_XML_DEBUG' in os.environ:
    verbose = 1
else:
    verbose = 0
if 'LDTP_WINDOWS' in os.environ or (sys.platform.find('darwin') == -1 and
                                    sys.platform.find('win') != -1):
    if 'LDTP_LINUX' in os.environ:
        _ldtp_windows_env = False
    else:
        _ldtp_windows_env = True
else:
   _ldtp_windows_env = False

class _Method(xmlrpclib._Method):
    def __call__(self, *args, **kwargs):
        if _ldtp_debug:
            logger.debug('%s(%s)' % (self.__name, \
                                         ', '.join(map(repr, args) + ['%s=%s' % (k, repr(v)) \
                                                                          for k, v in kwargs.items()])))
        return self.__send(self.__name, args[1:])

class Transport(xmlrpclib.Transport):
    def _handle_signal(self, signum, frame):
        if _ldtp_debug:
            if signum == signal.SIGCHLD:
                print("ldtpd exited!")
            elif signum == signal.SIGUSR1:
                print("SIGUSR1 received. ldtpd ready for requests.")
            elif signum == signal.SIGALRM:
                print("SIGALRM received. Timeout waiting for SIGUSR1.")

    def _spawn_daemon(self):
        pid = os.getpid()
        if _ldtp_windows_env:
            if _ldtp_debug:
                cmd = 'start cmd /K CobraWinLDTP.exe'
            else:
                cmd = 'CobraWinLDTP.exe'
            subprocess.Popen(cmd, shell = True)
            self._daemon = True
        elif platform.mac_ver()[0] != '':
            pycmd = 'import atomac.ldtpd; atomac.ldtpd.main(parentpid=%s)' % pid
            self._daemon = os.spawnlp(os.P_NOWAIT, 'python',
                                      'python', '-c', pycmd)
        else:
            pycmd = 'import ldtpd; ldtpd.main(parentpid=%s)' % pid
            self._daemon = os.spawnlp(os.P_NOWAIT, 'python',
                                      'python', '-c', pycmd)
    # http://www.itkovian.net/base/transport-class-for-pythons-xml-rpc-lib/
    ##
    # Connect to server.
    #
    # @param host Target host.
    # @return A connection handle.

    if not _python26:
        # Add to the class, only if > python 2.5
        def make_connection(self, host):
            # create a HTTP connection object from a host descriptor
            import httplib
            host, extra_headers, x509 = self.get_host_info(host)
            return httplib.HTTPConnection(host)
    ##
    # Send a complete request, and parse the response.
    #
    # @param host Target host.
    # @param handler Target PRC handler.
    # @param request_body XML-RPC request body.
    # @param verbose Debugging flag.
    # @return XML response.

    def request(self, host, handler, request_body, verbose=0):
        # issue XML-RPC request
        retry_count = 1
        while True:
            try:
                if _python26:
                    # Noticed this in Hutlab environment (Windows 7 SP1)
                    # Activestate python 2.5, use the old method
                    return xmlrpclib.Transport.request(
                        self, host, handler, request_body, verbose=verbose)
                # Follwing implementation not supported in Python <= 2.6
                h = self.make_connection(host)
                if verbose:
                    h.set_debuglevel(1)

                self.send_request(h, handler, request_body)
                self.send_host(h, host)
                self.send_user_agent(h)
                self.send_content(h, request_body)

                response = h.getresponse()

                if response.status != 200:
                    raise xmlrpclib.ProtocolError(host + handler, response.status,
                                        response.reason, response.msg.headers)

                payload = response.read()
                parser, unmarshaller = self.getparser()
                parser.feed(payload)
                parser.close()

                return unmarshaller.close()
            except SocketError as e:
                if ((_ldtp_windows_env and e[0] == 10061) or \
                        (hasattr(e, 'errno') and (e.errno == 111 or \
                                                      e.errno == 61 or \
                                                      e.errno == 146))) \
                        and 'localhost' in host:
                    if hasattr(self, 'close'):
                        # On Windows XP SP3 / Python 2.5, close doesn't exist
                        self.close()
                    if retry_count == 1:
                        retry_count += 1
                        if not _ldtp_windows_env:
                            sigusr1 = signal.signal(signal.SIGUSR1, self._handle_signal)
                            sigalrm = signal.signal(signal.SIGALRM, self._handle_signal)
                            sigchld = signal.signal(signal.SIGCHLD, self._handle_signal)
                        self._spawn_daemon()
                        if _ldtp_windows_env:
                            time.sleep(5)
                        else:
                            signal.alarm(15) # Wait 15 seconds for ldtpd
                            signal.pause()
                            # restore signal handlers
                            signal.alarm(0)
                            signal.signal(signal.SIGUSR1, sigusr1)
                            signal.signal(signal.SIGALRM, sigalrm)
                            signal.signal(signal.SIGCHLD, sigchld)
                        continue
                    else:
                        raise
                # else raise exception
                raise
            except xmlrpclib.Fault as e:
                if hasattr(self, 'close'):
                    self.close()
                if e.faultCode == ERROR_CODE:
                    raise LdtpExecutionError(e.faultString.encode('utf-8'))
                else:
                    raise e

    def __del__(self):
        self.kill_daemon()

    def kill_daemon(self):
        try:
            if _ldtp_windows_env and self._daemon:
                # If started by the current current, then terminate
                # else, silently quit
                subprocess.Popen('taskkill /F /IM CobraWinLDTP.exe',
                                 shell = True, stdout = subprocess.PIPE,
                                 stderr = subprocess.PIPE).communicate()
            else:
                os.kill(self._daemon, signal.SIGKILL)
        except AttributeError:
            pass

class LdtpClient(xmlrpclib.ServerProxy):
    def __init__(self, uri, encoding=None, verbose=0, use_datetime=0):
        xmlrpclib.ServerProxy.__init__(
            self, uri, Transport(), encoding, verbose, 1, use_datetime)

    def __getattr__(self, name):
        # magic method dispatcher
        return _Method(self._ServerProxy__request, name)

    def kill_daemon(self):
        self._ServerProxy__transport.kill_daemon()

    def setHost(self, host):
        setattr(self, '_ServerProxy__host', host)

class ooldtp:
    def __init__(self, server='localhost', port=4118):
        self._pollEvents = None
        self._file_logger = None
        # Add handler to root logger
        self.logger = logging.getLogger('')
        self._client = LdtpClient('http://%s:%s' % (server, port),
                                  verbose = verbose)
        atexit.register(self._client.kill_daemon)
        self._populateNamespace()
        self._pollEvents = PollEvents(self)
        thread.start_new_thread(self._pollEvents.run, ())
        self._pollLogs = PollLogs(self)
        thread.start_new_thread(self._pollLogs.run, ())

    def setHost(self, host):
        self._client.setHost(host)

    def whoismyhost(self):
        return self._client._ServerProxy__host

    def addloghandler(self, handler):
        """
        Add custom log handler
        @param handler: Handler instance
        @type handler: object
    
        @return: 1 on success and 0 on error
        @rtype: integer
        """
        self.logger.addHandler(handler)
        return 1
    
    def removeloghandler(self, handler):
        """
        Remove custom log handler
        @param handler: Handler instance
        @type handler: object
    
        @return: 1 on success and 0 on error
        @rtype: integer
        """
        self.logger.removeHandler(handler)
        return 1
    
    def log(self, message, level = logging.DEBUG):
        """
        Logs the message in the root logger with the log level
        @param message: Message to be logged
        @type message: string
        @param level: Log level, defaul DEBUG
        @type level: integer
    
        @return: 1 on success and 0 on error
        @rtype: integer
        """
        if _ldtp_debug:
            print(message)
        self.logger.log(level, str(message))
        return 1
    
    def startlog(self, filename, overwrite = True):
        """
        @param filename: Start logging on the specified file
        @type filename: string
        @param overwrite: Overwrite or append
            False - Append log to an existing file
            True - Write log to a new file. If file already exist, 
            then erase existing file content and start log
        @type overwrite: boolean
    
        @return: 1 on success and 0 on error
        @rtype: integer
        """

        if not filename:
            return 0

        if overwrite:
            # Create new file, by overwriting existing file
            _mode = 'w'
        else:
            # Append existing file
            _mode = 'a'
        # Create logging file handler
        self._file_logger = self.logging.FileHandler(os.path.expanduser(filename), _mode)
        # Log 'Levelname: Messages', eg: 'ERROR: Logged message'
        _formatter = self.logging.Formatter('%(levelname)-8s: %(message)s')
        self._file_logger.setFormatter(_formatter)
        self.logger.addHandler(_file_logger)
        if _ldtp_debug:
            # On debug, change the default log level to DEBUG
            self._file_logger.setLevel(logging.DEBUG)
        else:
            # else log in case of ERROR level and above
            self._file_logger.setLevel(logging.ERROR)
        return 1
    
    def stoplog(self):
        """ Stop logging.
    
        @return: 1 on success and 0 on error
        @rtype: integer
        """
        if self._file_logger:
            self.logger.removeHandler(_file_logger)
            self._file_logger = None
        return 1

    def logFailures(self, *args):
        # Do nothing. For backward compatability
        warnings.warn('Use Mago framework - http://mago.ubuntu.com', DeprecationWarning)

    #internally bind a function as a method of self's class -- note that this one has issues!
    def _addmethod(self, method, name):
        # Reference:
        # http://stackoverflow.com/questions/972/adding-a-method-to-an-existing-object
        self.__dict__[name] = types.MethodType( method, self.__class__ )

    def _populateNamespace(self):
        for method in self._client.system.listMethods():
            if method.startswith('system.'):
                continue
            if method in dir(self):
                local_name = '_remote_' + method
            else:
                local_name = method
            self._addmethod(getattr(self._client, method), local_name)

    def imagecapture(self, window_name = None, out_file = None, x = 0, y = 0,
                     width = None, height = None):
        """
        Captures screenshot of the whole desktop or given window

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param x: x co-ordinate value
        @type x: integer
        @param y: y co-ordinate value
        @type y: integer
        @param width: width co-ordinate value
        @type width: integer
        @param height: height co-ordinate value
        @type height: integer

        @return: screenshot filename
        @rtype: string
        """
        if not out_file:
            out_file = tempfile.mktemp('.png', 'ldtp_')
        else:
            out_file = os.path.expanduser(out_file)

        ### Windows compatibility
        if _ldtp_windows_env:
            if width == None:
                width = -1
            if height == None:
                height = -1
            if window_name == None:
                window_name = ''
        ### Windows compatibility - End
        data = self._remote_imagecapture(window_name, x, y, width, height)
        f = open(out_file, 'wb')
        f.write(b64decode(data))
        f.close()
        return out_file

    def wait(self, timeout=5):
        return self._remote_wait(timeout)
    def waittillguiexist(self, window_name, object_name = '',
                         guiTimeOut = 30, state = ''):
        return self._remote_waittillguiexist(window_name, object_name,
                                             guiTimeOut)
    def waittillguinotexist(self, window_name, object_name = '',
                            guiTimeOut = 30, state = ''):
        return self._remote_waittillguinotexist(window_name, object_name,
                                                guiTimeOut)
    def guiexist(self, window_name, object_name = ''):
        return self._remote_guiexist(window_name, object_name)
    def launchapp(self, cmd, args = [], delay = 0, env = 1, lang = "C"):
        return self._remote_launchapp(cmd, args, delay, env, lang)
    def hasstate(self, window_name, object_name, state, guiTimeOut = 0):
        return self._remote_hasstate(window_name, object_name, state, guiTimeOut)
    def selectrow(self, window_name, object_name, row_text):
        return self._remote_selectrow(window_name, object_name, row_text, False)
    def doesrowexist(self, window_name, object_name, row_text, partial_match = False):
        return self._remote_doesrowexist(window_name, object_name, row_text, partial_match)
    def getchild(self, window_name, child_name = '', role = '', parent = ''):
        return self._remote_getchild(window_name, child_name, role, parent)
    def enterstring(self, window_name, object_name = '', data = ''):
        return self._remote_enterstring(window_name, object_name, data)
    def setvalue(self, window_name, object_name, data):
        return self._remote_setvalue(window_name, object_name, float(data))
    def grabfocus(self, window_name, object_name = ''):
        # On Linux just with window name, grab focus doesn't work
        # So, we can't make this call generic
        return self._remote_grabfocus(window_name, object_name)
    def copytext(self, window_name, object_name, start, end = -1):
        return self._remote_copytext(window_name, object_name, start, end)
    def cuttext(self, window_name, object_name, start, end = -1):
        return self._remote_cuttext(window_name, object_name, start, end)
    def deletetext(self, window_name, object_name, start, end = -1):
        return self._remote_deletetext(window_name, object_name, start, end)
    def startprocessmonitor(self, process_name, interval = 2):
        return self._remote_startprocessmonitor(process_name, interval)
    def gettextvalue(self, window_name, object_name, startPosition = 0, endPosition = 0):
        return self._remote_gettextvalue(window_name, object_name, startPosition, endPosition)
    def getcellvalue(self, window_name, object_name, row_index, column = 0):
        return self._remote_getcellvalue(window_name, object_name, row_index, column)
    def getcellsize(self, window_name, object_name, row_index, column = 0):
        return self._remote_getcellsize(window_name, object_name, row_index, column)
    def getobjectnameatcoords(self, waitTime = 0):
        # FIXME: Yet to implement in Mac, works on Windows/Linux
        return self._remote_getobjectnameatcoords(waitTime)

    def onwindowcreate(self, window_name, fn_name, *args):
        """
        On window create, call the function with given arguments

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param fn_name: Callback function
        @type fn_name: function
        @param *args: arguments to be passed to the callback function
        @type *args: var args

        @return: 1 if registration was successful, 0 if not.
        @rtype: integer
        """
        self._pollEvents._callback[window_name] = ["onwindowcreate", fn_name, args]
        return self._remote_onwindowcreate(window_name)
    
    def removecallback(self, window_name):
        """
        Remove registered callback on window create

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: 1 if registration was successful, 0 if not.
        @rtype: integer
        """
        if window_name in self._pollEvents._callback:
            del self._pollEvents._callback[window_name]
        return self._remote_removecallback(window_name)

    def registerevent(self, event_name, fn_name, *args):
        """
        Register at-spi event

        @param event_name: Event name in at-spi format.
        @type event_name: string
        @param fn_name: Callback function
        @type fn_name: function
        @param *args: arguments to be passed to the callback function
        @type *args: var args

        @return: 1 if registration was successful, 0 if not.
        @rtype: integer
        """
        if not isinstance(event_name, str):
            raise ValueError("event_name should be string")
        self._pollEvents._callback[event_name] = [event_name, fn_name, args]
        return self._remote_registerevent(event_name)

    def deregisterevent(self, event_name):
        """
        Remove callback of registered event

        @param event_name: Event name in at-spi format.
        @type event_name: string

        @return: 1 if registration was successful, 0 if not.
        @rtype: integer
        """

        if event_name in self._pollEvents._callback:
            del self._pollEvents._callback[event_name]
        return self._remote_deregisterevent(event_name)

    def registerkbevent(self, keys, modifiers, fn_name, *args):
        """
        Register keystroke events

        @param keys: key to listen
        @type keys: string
        @param modifiers: control / alt combination using gtk MODIFIERS
        @type modifiers: int
        @param fn_name: Callback function
        @type fn_name: function
        @param *args: arguments to be passed to the callback function
        @type *args: var args

        @return: 1 if registration was successful, 0 if not.
        @rtype: integer
        """
        event_name = "kbevent%s%s" % (keys, modifiers)
        self._pollEvents._callback[event_name] = [event_name, fn_name, args]
        return self._remote_registerkbevent(keys, modifiers)
    
    def deregisterkbevent(self, keys, modifiers):
        """
        Remove callback of registered event

        @param keys: key to listen
        @type keys: string
        @param modifiers: control / alt combination using gtk MODIFIERS
        @type modifiers: int

        @return: 1 if registration was successful, 0 if not.
        @rtype: integer
        """

        event_name = "kbevent%s%s" % (keys, modifiers)
        if event_name in _pollEvents._callback:
            del _pollEvents._callback[event_name]
        return self._remote_deregisterkbevent(keys, modifiers)

    def windowuptime(self, window_name):
        """
        Get window uptime

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
    
        @return: "starttime, endtime" as datetime python object
        """
        tmp_time = self._remote_windowuptime(window_name)
        if tmp_time:
            tmp_time = tmp_time.split('-')
            start_time = tmp_time[0].split(' ')
            end_time = tmp_time[1].split(' ')
            _start_time = datetime.datetime(int(start_time[0]), int(start_time[1]),
                                            int(start_time[2]), int(start_time[3]),
                                            int(start_time[4]), int(start_time[5]))
            _end_time = datetime.datetime(int(end_time[0]), int(end_time[1]),
                                          int(end_time[2]),int(end_time[3]),
                                          int(end_time[4]), int(end_time[5]))
            return _start_time, _end_time
        return None

class PollLogs:
    """
    Class to poll logs, NOTE: *NOT* for external use
    """
    def __init__(self, ooldtp):
        self._stop = False
        self._ooldtp = ooldtp

    def __del__(self):
        """
        Stop polling when destroying this class
        """
        self._stop = True

    def run(self):
        while not self._stop:
            try:
                if not self.poll_server():
                    # Socket error
                    break
            except:
                self._ooldtp.log(traceback.format_exc())
                self._stop = False
                break

    def poll_server(self):
        if not self._ooldtp.logger.handlers:
            # If no handlers registered don't call the getlastlog
            # as it will flush out all the logs
            time.sleep(1)
            return True
        try:
            message = self._ooldtp.getlastlog()
        except socket.error:
            t = traceback.format_exc()
            self._ooldtp.log(t)
            # Connection to server might be failed
            return False

        if not message:
            # No log in queue, sleep a second
            time.sleep(1)
            return True
        # Split message type and message
        message_type, message = re.split('-', message, 1)
        if re.match('MEMINFO', message_type, re.I):
            level = LDTP_LOG_MEMINFO
        elif re.match('CPUINFO', message_type, re.I):
            level = LDTP_LOG_CPUINFO
        elif re.match('INFO', message_type, re.I):
            level = logging.INFO
        elif re.match('WARNING', message_type, re.I):
            level = logging.WARNING
        elif re.match('ERROR', message_type, re.I):
            level = logging.ERROR
        elif re.match('CRITICAL', message_type, re.I):
            level = logging.CRITICAL
        else:
            level = logging.DEBUG
        # Log the messsage with the attained level
        self._ooldtp.log(message, level)
        return True

class PollEvents:
    """
    Class to poll callback events, NOTE: *NOT* for external use
    """
    def __init__(self, ooldtp):
        self._stop = False
        self._ooldtp = ooldtp
        # Initialize callback dictionary
        self._callback = {}

    def __del__(self):
        """
        Stop callback when destroying this class
        """
        self._stop = True

    def run(self):
        while not self._stop:
            try:
                if not self.poll_server():
                    # Socket error
                    break
            except:
                self.ooldtp.log(traceback.format_exc())
                self._stop = False
                break

    def poll_server(self):
        if not self._callback:
            # If callback not registered, don't proceed further
            # Sleep a second and then return
            time.sleep(1)
            return True
        try:
            event = self._ooldtp.poll_events()
        except socket.error:
            self._ooldtp.log(traceback.format_exc())
            # Connection to server might be failed
            return False

        if not event:
            # No event in queue, sleep a second
            time.sleep(1)
            return True

        # Event format:
        # window:create-Untitled Document 1 - gedit
        event = event.split('-', 1) # Split first -
        data = event[1] # Rest of data
        event_type = event[0] # event type
        # self._callback[name][0] - Event type
        # self._callback[name][1] - Callback function
        # self._callback[name][2] - Arguments to callback function
        for name in self._callback:
            # Window created event
            # User registered window events
            # Keyboard event
            if (event_type == "onwindowcreate" and \
                re.match(glob_trans(name), data, re.M | re.U | re.L)) or \
                (event_type != "onwindowcreate" and \
                 self._callback[name][0] == event_type) or \
                 event_type == 'kbevent':
                if event_type == 'kbevent':
                    # Special case
                    keys, modifiers = data.split('-')
                    fname = 'kbevent%s%s' % (keys, modifiers)
                else:
                    fname = name
                # Get the callback function
                callback = self._callback[fname][1]
                if not callable(callback):
                    # If not callable, ignore the event
                    continue
                args = self._callback[fname][2]
                try:
                    if len(args) and args[0]:
                        # Spawn a new thread, for each event
                        # If one or more arguments to the callback function
                        thread.start_new_thread(callback, args)
                    else:
                        # Spawn a new thread, for each event
                        # No arguments to the callback function
                        thread.start_new_thread(callback, ())
                except:
                    # Log trace incase of exception
                    self._ooldtp.log(traceback.format_exc())
                    # Silently ignore !?! any exception thrown
                    pass
                # When multiple kb events registered, the for
                # loop keeps iterating, so just break the loop
                break
        return True
