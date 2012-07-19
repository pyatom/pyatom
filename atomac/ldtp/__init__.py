# Copyright (c) 2012 VMware, Inc. All Rights Reserved.

# This file is part of ATOMac.

#@author: Nagappan Alagappan <nagappan@gmail.com>                                                                                                      
#@copyright: Copyright (c) 2009-12 Nagappan Alagappan                                                                                                  

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
import time
import state
import client
import atexit
import socket
import thread
import logging
import datetime
import tempfile
import warnings
import traceback
from base64 import b64decode
from fnmatch import translate as glob_trans
from client_exception import LdtpExecutionError

_pollEvents = None
_file_logger = None
_ldtp_debug = client._ldtp_debug
_ldtp_windows_env = client._ldtp_windows_env

if 'LDTP_DEBUG' in os.environ:
    _ldtp_debug = os.environ['LDTP_DEBUG']

def setHost(host):
    client._client.setHost(host)

def whoismyhost():
    return client._client._ServerProxy__host

LDTP_LOG_MEMINFO = 60
LDTP_LOG_CPUINFO = 61
logging.addLevelName(LDTP_LOG_MEMINFO, 'MEMINFO')
logging.addLevelName(LDTP_LOG_CPUINFO, 'CPUINFO')

# Add handler to root logger
logger = logging.getLogger('')

def addloghandler(handler):
    """
    Add custom log handler
    @param handler: Handler instance
    @type handler: object

    @return: 1 on success and 0 on error
    @rtype: integer
    """

    logger.addHandler(handler)
    return 1

def removeloghandler(handler):
    """
    Remove custom log handler
    @param handler: Handler instance
    @type handler: object

    @return: 1 on success and 0 on error
    @rtype: integer
    """

    logger.removeHandler(handler)
    return 1

def log(message, level = logging.DEBUG):
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
        print message
    logger.log(level, str(message))
    return 1

def startlog(filename, overwrite = True):
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
    global _file_logger
    # Create logging file handler
    _file_logger = logging.FileHandler(os.path.expanduser(filename), _mode)
    # Log 'Levelname: Messages', eg: 'ERROR: Logged message'
    _formatter = logging.Formatter(u'%(levelname)-8s: %(message)s')
    _file_logger.setFormatter(_formatter)
    logger.addHandler(_file_logger)
    if _ldtp_debug:
        # On debug, change the default log level to DEBUG
        _file_logger.setLevel(logging.DEBUG)
    else:
        # else log in case of ERROR level and above
        _file_logger.setLevel(logging.ERROR)

    return 1

def stoplog():
    """ Stop logging.

    @return: 1 on success and 0 on error
    @rtype: integer
    """

    global _file_logger
    if _file_logger:
        logger.removeHandler(_file_logger)
        _file_logger = None
    return 1

class PollLogs:
    """
    Class to poll logs, NOTE: *NOT* for external use
    """
    global _file_logger
    def __init__(self):
        self._stop = False

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
                log(traceback.format_exc())
                self._stop = False
                break

    def poll_server(self):
        if not logger.handlers:
            # If no handlers registered don't call the getlastlog
            # as it will flush out all the logs
            time.sleep(1)
            return True
        try:
            message = getlastlog()
        except socket.error:
            t = traceback.format_exc()
            log(t)
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
        log(message, level)
        return True

def logFailures(*args):
    # Do nothing. For backward compatability
    warnings.warn('Use Mago framework - http://mago.ubuntu.com', DeprecationWarning)
    pass

def _populateNamespace(d):
    for method in client._client.system.listMethods():
        if method.startswith('system.'):
            continue
        if method in d:
            local_name = '_remote_' + method
        else:
            local_name = method
        d[local_name] = getattr(client._client, method)
        d[local_name].__doc__ = client._client.system.methodHelp(method)

class PollEvents:
    """
    Class to poll callback events, NOTE: *NOT* for external use
    """
    def __init__(self):
        self._stop = False
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
                log(traceback.format_exc())
                self._stop = False
                break

    def poll_server(self):
        if not self._callback:
            # If callback not registered, don't proceed further
            # Sleep a second and then return
            time.sleep(1)
            return True
        try:
            event = poll_events()
        except socket.error:
            log(traceback.format_exc())
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
                    log(traceback.format_exc())
                    # Silently ignore !?! any exception thrown
                    pass
                # When multiple kb events registered, the for
                # loop keeps iterating, so just break the loop
                break
        return True

def imagecapture(window_name = None, out_file = None, x = 0, y = 0,
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
    data = _remote_imagecapture(window_name, x, y, width, height)
    f = open(out_file, 'wb')
    f.write(b64decode(data))
    f.close()

    return out_file

### WINDOWS
### XML-RPC.NET doesn't support optional arguments
### We have to wrap those wrappers locally
if _ldtp_windows_env:
    def wait(timeout=5):
        return _remote_wait(timeout)
    def waittillguiexist(window_name, object_name = '',
                         guiTimeOut = 30, state = ''):
        return _remote_waittillguiexist(window_name, object_name,
                                        guiTimeOut)
    
    def waittillguinotexist(window_name, object_name = '',
                            guiTimeOut = 30, state = ''):
        return _remote_waittillguinotexist(window_name, object_name,
                                           guiTimeOut)
    def guiexist(window_name, object_name = ''):
        return _remote_guiexist(window_name, object_name)
    def launchapp(cmd, args = [], delay = 0, env = 1, lang = "C"):
        return _remote_launchapp(cmd, args, delay, env, lang)
    def hasstate(window_name, object_name, state, guiTimeOut = 0):
        return _remote_hasstate(window_name, object_name, state, guiTimeOut)
    def selectrow(window_name, object_name, row_text):
        return _remote_selectrow(window_name, object_name, row_text, False)
    def getchild(window_name, child_name = '', role = '', parent = ''):
        return _remote_getchild(window_name, child_name, role, parent)
    def enterstring(window_name, object_name = '', data = ''):
        return _remote_enterstring(window_name, object_name, data)
    def setvalue(window_name, object_name, data):
        return _remote_setvalue(window_name, object_name, float(data))
    def grabfocus(window_name, object_name = ''):
        # On Linux just with window name, grab focus doesn't work
        # So, we can't make this call generic
        return _remote_grabfocus(window_name, object_name)
    def copytext(window_name, object_name, start, end = -1):
        return _remote_copytext(window_name, object_name, start, end)
    def cuttext(window_name, object_name, start, end = -1):
        return _remote_cuttext(window_name, object_name, start, end)
    def deletetext(window_name, object_name, start, end = -1):
        return _remote_deletetext(window_name, object_name, start, end)
    def startprocessmonitor(process_name, interval = 2):
        return _remote_startprocessmonitor(process_name, interval)
    def gettextvalue(window_name, object_name, startPosition = 0, endPosition = 0):
        return _remote_gettextvalue(window_name, object_name, startPosition, endPosition)
### WINDOWS

def onwindowcreate(window_name, fn_name, *args):
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

    _pollEvents._callback[window_name] = ["onwindowcreate", fn_name, args]
    return _remote_onwindowcreate(window_name)

def removecallback(window_name):
    """
    Remove registered callback on window create

    @param window_name: Window name to look for, either full name,
    LDTP's name convention, or a Unix glob.
    @type window_name: string

    @return: 1 if registration was successful, 0 if not.
    @rtype: integer
    """

    if window_name in _pollEvents._callback:
        del _pollEvents._callback[window_name]
    return _remote_removecallback(window_name)

def registerevent(event_name, fn_name, *args):
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
        raise ValueError, "event_name should be string"
    _pollEvents._callback[event_name] = [event_name, fn_name, args]
    return _remote_registerevent(event_name)

def deregisterevent(event_name):
    """
    Remove callback of registered event

    @param event_name: Event name in at-spi format.
    @type event_name: string

    @return: 1 if registration was successful, 0 if not.
    @rtype: integer
    """

    if event_name in _pollEvents._callback:
        del _pollEvents._callback[event_name]
    return _remote_deregisterevent(event_name)

def registerkbevent(keys, modifiers, fn_name, *args):
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
    event_name = u"kbevent%s%s" % (keys, modifiers)
    _pollEvents._callback[event_name] = [event_name, fn_name, args]
    return _remote_registerkbevent(keys, modifiers)

def deregisterkbevent(keys, modifiers):
    """
    Remove callback of registered event

    @param keys: key to listen
    @type keys: string
    @param modifiers: control / alt combination using gtk MODIFIERS
    @type modifiers: int

    @return: 1 if registration was successful, 0 if not.
    @rtype: integer
    """

    event_name = u"kbevent%s%s" % (keys, modifiers)
    if event_name in _pollEvents._callback:
        del _pollEvents._callback[event_name]
    return _remote_deregisterkbevent(keys, modifiers)

def windowuptime(window_name):
    """
    Get window uptime
    
    @param window_name: Window name to look for, either full name,
    LDTP's name convention, or a Unix glob.
    @type window_name: string

    @return: "starttime, endtime" as datetime python object
    """

    tmp_time = _remote_windowuptime(window_name)
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

_populateNamespace(globals())
#_pollEvents = PollEvents()
#thread.start_new_thread(_pollEvents.run, ())
#_pollLogs = PollLogs()
#thread.start_new_thread(_pollLogs.run, ())

atexit.register(client._client.kill_daemon)
