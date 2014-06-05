# -*- coding: utf-8 -*-
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
"""Core class to be exposed via XMLRPC in LDTP daemon."""

import re
import time
import atomac
import fnmatch
import traceback

from menu import Menu
from text import Text
from mouse import Mouse
from table import Table
from value import Value
from generic import Generic
from combo_box import ComboBox
from constants import ldtp_class_type
from page_tab_list import PageTabList
from utils import Utils, ProcessStats
from server_exception import LdtpServerException

try:
    import psutil
except ImportError:
    pass

class Core(ComboBox, Menu, Mouse, PageTabList, Text, Table, Value, Generic):
    def __init__(self):
        super(Core, self).__init__()
        self._process_stats={}

    def __del__(self):
        for key in self._process_stats.keys():
            # Stop all process monitoring instances
            self._process_stats[key].stop()

    """Core LDTP class"""
    def appundertest(self, app_name):
        """
        Application under test
        app_name: Application name should be app identifier
        eg: com.apple.AppleSpell', 'com.apple.talagent', 'com.apple.dock',
        'com.adiumX.adiumX', 'com.apple.notificationcenterui', 'org.3rddev.xchatazure',
        'com.skype.skype', 'com.mcafee.McAfeeReporter', 'com.microsoft.outlook.database_daemon',
        'com.apple.photostream-agent', 'com.google.GoogleTalkPluginD',
        'com.microsoft.SyncServicesAgent', 'com.google.Chrome.helper.EH',
        'com.apple.dashboard.client', 'None', 'com.vmware.fusionStartMenu',
        'com.apple.ImageCaptureExtension2', 'com.apple.loginwindow', 'com.mozypro.status',
        'com.apple.Preview', 'com.google.Chrome.helper', 'com.apple.calculator',
        'com.apple.Terminal', 'com.apple.iTunesHelper', 'com.apple.ActivityMonitor',
        'net.juniper.NetworkConnect', 'com.google.Chrome', 'com.apple.dock.extra',
        'com.apple.finder', 'com.yourcompany.Menulet', 'com.apple.systemuiserver'

        @return: return 1 on success
        @rtype: int
        """
        self._app_under_test=app_name
        return 1

    def getapplist(self):
        """
        Get all accessibility application name that are currently running

        @return: list of appliction name of string type on success.
        @rtype: list
        """
        app_list=[]
        # Update apps list, before parsing the list
        self._update_apps()
        for gui in self._running_apps:
            name=gui.localizedName()
            # default type was objc.pyobjc_unicode
            # convert to Unicode, else exception is thrown
            # TypeError: "cannot marshal <type 'objc.pyobjc_unicode'> objects"
            try:
                name=unicode(name)
            except UnicodeEncodeError:
                pass
            app_list.append(name)
        # Return unique application list
        return list(set(app_list))

    def getwindowlist(self):
        """
        Get all accessibility window that are currently open

        @return: list of window names in LDTP format of string type on success.
        @rtype: list
        """
        return self._get_windows(True).keys()

    def isalive(self):
        """
        Client will use this to verify whether the server instance is alive or not.

        @return: True on success.
        @rtype: boolean
        """
        return True

    def poll_events(self):
        """
        Poll for any registered events or window create events

        @return: window name
        @rtype: string
        """

        if not self._callback_event:
            return ''
        return self._callback_event.pop()

    def getlastlog(self):
        """
        Returns one line of log at any time, if any available, else empty string

        @return: log as string
        @rtype: string
        """

        if not self._custom_logger.log_events:
            return ''

        return self._custom_logger.log_events.pop()

    def startprocessmonitor(self, process_name, interval=2):
        """
        Start memory and CPU monitoring, with the time interval between
        each process scan

        @param process_name: Process name, ex: firefox-bin.
        @type process_name: string
        @param interval: Time interval between each process scan
        @type interval: double

        @return: 1 on success
        @rtype: integer
        """
        if self._process_stats.has_key(process_name):
            # Stop previously running instance
            # At any point, only one process name can be tracked
            # If an instance already exist, then stop it
            self._process_stats[process_name].stop()
        # Create an instance of process stat
        self._process_stats[process_name]=ProcessStats(process_name, interval)
        # start monitoring the process
        self._process_stats[process_name].start()
        return 1

    def stopprocessmonitor(self, process_name):
        """
        Stop memory and CPU monitoring

        @param process_name: Process name, ex: firefox-bin.
        @type process_name: string

        @return: 1 on success
        @rtype: integer
        """
        if self._process_stats.has_key(process_name):
            # Stop monitoring process
            self._process_stats[process_name].stop()
        return 1

    def getcpustat(self, process_name):
        """
        get CPU stat for the give process name

        @param process_name: Process name, ex: firefox-bin.
        @type process_name: string

        @return: cpu stat list on success, else empty list
                If same process name, running multiple instance,
                get the stat of all the process CPU usage
        @rtype: list
        """
        # Create an instance of process stat
        _stat_inst=ProcessStats(process_name)
        _stat_list=[]
        for p in _stat_inst.get_cpu_memory_stat():
            try:
                _stat_list.append(p.get_cpu_percent())
            except psutil.AccessDenied:
                pass
        return _stat_list

    def getmemorystat(self, process_name):
        """
        get memory stat

        @param process_name: Process name, ex: firefox-bin.
        @type process_name: string

        @return: memory stat list on success, else empty list
                If same process name, running multiple instance,
                get the stat of all the process memory usage
        @rtype: list
        """
        # Create an instance of process stat
        _stat_inst=ProcessStats(process_name)
        _stat_list=[]
        for p in _stat_inst.get_cpu_memory_stat():
            # Memory percent returned with 17 decimal values
            # ex: 0.16908645629882812, round it to 2 decimal values
            # as 0.03
            try:
                _stat_list.append(round(p.get_memory_percent(), 2))
            except psutil.AccessDenied:
                pass
        return _stat_list

    def getobjectlist(self, window_name):
        """
        Get list of items in given GUI.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: list of items in LDTP naming convention.
        @rtype: list
        """
        try:
            window_handle, name, app=self._get_window_handle(window_name, True)
            object_list=self._get_appmap(window_handle, name, True)
        except atomac._a11y.ErrorInvalidUIElement:
            # During the test, when the window closed and reopened
            # ErrorInvalidUIElement exception will be thrown
            self._windows={}
            # Call the method again, after updating apps
            window_handle, name, app=self._get_window_handle(window_name, True)
            object_list=self._get_appmap(window_handle, name, True)
        return object_list.keys()

    def getobjectinfo(self, window_name, object_name):
        """
        Get object properties.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string

        @return: list of properties
        @rtype: list
        """
        try:
            obj_info=self._get_object_map(window_name, object_name,
                                          wait_for_object=False)
        except atomac._a11y.ErrorInvalidUIElement:
            # During the test, when the window closed and reopened
            # ErrorInvalidUIElement exception will be thrown
            self._windows={}
            # Call the method again, after updating apps
            obj_info=self._get_object_map(window_name, object_name,
                                          wait_for_object=False)
        props = []
        if obj_info:
            for obj_prop in obj_info.keys():
                if not obj_info[obj_prop] or obj_prop == "obj":
                    # Don't add object handle to the list
                    continue
                props.append(obj_prop)
        return props

    def getobjectproperty(self, window_name, object_name, prop):
        """
        Get object property value.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string
        @param prop: property name.
        @type prop: string

        @return: property
        @rtype: string
        """
        try:
            obj_info=self._get_object_map(window_name, object_name,
                                          wait_for_object=False)
        except atomac._a11y.ErrorInvalidUIElement:
            # During the test, when the window closed and reopened
            # ErrorInvalidUIElement exception will be thrown
            self._windows={}
            # Call the method again, after updating apps
            obj_info=self._get_object_map(window_name, object_name,
                                          wait_for_object=False)
        if obj_info and prop != "obj" and prop in obj_info:
            if prop == "class":
                # ldtp_class_type are compatible with Linux and Windows class name
                # If defined class name exist return that,
                # else return as it is
                return ldtp_class_type.get(obj_info[prop], obj_info[prop])
            else:
                return obj_info[prop]
        raise LdtpServerException('Unknown property "%s" in %s' % \
                                      (prop, object_name))

    def getchild(self, window_name, child_name = '', role = '', parent = ''):
        """
        Gets the list of object available in the window, which matches
        component name or role name or both.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param child_name: Child name to search for.
        @type child_name: string
        @param role: role name to search for, or an empty string for wildcard.
        @type role: string
        @param parent: parent name to search for, or an empty string for wildcard.
        @type role: string
        @return: list of matched children names
        @rtype: list
        """
        matches = []
        if role:
            role = re.sub(' ', '_', role)
        self._windows={}
        if parent and (child_name or role):
            _window_handle, _window_name = \
                self._get_window_handle(window_name)[0:2]
            if not _window_handle:
                raise LdtpServerException('Unable to find window "%s"' % \
                                              window_name)
            appmap = self._get_appmap(_window_handle, _window_name)
            obj = self._get_object_map(window_name, parent)
            def _get_all_children_under_obj(obj, child_list):
                if role and obj['class'] == role:
                    child_list.append(obj['label'])
                elif child_name and self._match_name_to_appmap(child_name, obj):
                    child_list.append(obj['label'])
                if obj:
                    children = obj['children']
                if not children:
                    return child_list
                for child in children.split():
                    return _get_all_children_under_obj( \
                        appmap[child],
                        child_list)

            matches = _get_all_children_under_obj(obj, [])
            if not matches:
                if child_name:
                    _name = 'name "%s" ' % child_name
                if role:
                    _role = 'role "%s" ' % role
                if parent:
                    _parent = 'parent "%s"' % parent
                exception = 'Could not find a child %s%s%s' % (_name, _role, _parent)
                raise LdtpServerException(exception)

            return matches

        _window_handle, _window_name = \
            self._get_window_handle(window_name)[0:2]
        if not _window_handle:
            raise LdtpServerException('Unable to find window "%s"' % \
                                          window_name)
        appmap = self._get_appmap(_window_handle, _window_name)
        for name in appmap.keys():
            obj = appmap[name]
            # When only role arg is passed
            if role and not child_name and obj['class'] == role:
                matches.append(name)
            # When parent and child_name arg is passed
            if parent and child_name and not role and \
                    self._match_name_to_appmap(parent, obj):
                matches.append(name)
            # When only child_name arg is passed
            if child_name and not role and \
                    self._match_name_to_appmap(child_name, obj):
                return name
                matches.append(name)
            # When role and child_name args are passed
            if role and child_name and obj['class'] == role and \
                    self._match_name_to_appmap(child_name, obj):
                matches.append(name)

        if not matches:
            _name = ''
            _role = ''
            _parent = ''
            if child_name:
                _name = 'name "%s" ' % child_name
            if role:
                _role = 'role "%s" ' % role
            if parent:
                _parent = 'parent "%s"' % parent
            exception = 'Could not find a child %s%s%s' % (_name, _role, _parent)
            raise LdtpServerException(exception)

        return matches

    def launchapp(self, cmd, args = [], delay = 0, env = 1, lang = "C"):
        """
        Launch application.

        @param cmd: Command line string to execute.
        @type cmd: string
        @param args: Arguments to the application
        @type args: list
        @param delay: Delay after the application is launched
        @type delay: int
        @param env: GNOME accessibility environment to be set or not
        @type env: int
        @param lang: Application language to be used
        @type lang: string

        @return: 1 on success
        @rtype: integer

        @raise LdtpServerException: When command fails
        """
        try:
            atomac.NativeUIElement.launchAppByBundleId(cmd)
            return 1
        except RuntimeError:
            if atomac.NativeUIElement.launchAppByBundlePath(cmd, args):
                # Let us wait so that the application launches
                try:
                    time.sleep(int(delay))
                except ValueError:
                    time.sleep(5)
                return 1
            else:
                raise LdtpServerException(u"Unable to find app '%s'" % cmd)

    def wait(self, timeout=5):
        """
        Wait a given amount of seconds.

        @param timeout: Wait timeout in seconds
        @type timeout: double

        @return: 1
        @rtype: integer
        """
        time.sleep(timeout)
        return 1

    def closewindow(self, window_name):
        """
        Close window.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: 1 on success.
        @rtype: integer
        """
        return self._singleclick(window_name, "btnclosebutton")

    def minimizewindow(self, window_name):
        """
        Minimize window.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: 1 on success.
        @rtype: integer
        """
        return self._singleclick(window_name, "btnminimizebutton")

    def maximizewindow(self, window_name):
        """
        Maximize window.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: 1 on success.
        @rtype: integer
        """
        return self._singleclick(window_name, "btnzoombutton")

    def activatewindow(self, window_name):
        """
        Activate window.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: 1 on success.
        @rtype: integer
        """
        window_handle=self._get_window_handle(window_name)
        self._grabfocus(window_handle)
        return 1

    def click(self, window_name, object_name):
        """
        Click item.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        size=self._getobjectsize(object_handle)
        self._grabfocus(object_handle)
        self.wait(0.5) 
        
        # If object doesn't support Press, trying clicking with the object
        # coordinates, where size=(x, y, width, height)
        # click on center of the widget
        # Noticed this issue on clicking AXImage
        # click('Instruments*', 'Automation')
        self.generatemouseevent(size[0] + size[2]/2, size[1] + size[3]/2, "b1c")
        return 1

    def getallstates(self, window_name, object_name):
        """
        Get all states of given object

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string

        @return: list of string on success.
        @rtype: list
        """
        object_handle=self._get_object_handle(window_name, object_name)
        _obj_states = []
        if object_handle.AXEnabled:
            _obj_states.append("enabled")
        if object_handle.AXFocused:
            _obj_states.append("focused")
        else:
            try:
                if object_handle.AXFocused:
                    _obj_states.append("focusable")
            except:
                pass
        if re.match("AXCheckBox", object_handle.AXRole, re.M | re.U | re.L) or \
                re.match("AXRadioButton", object_handle.AXRole,
                         re.M | re.U | re.L):
            if object_handle.AXValue:
                _obj_states.append("checked")
        return _obj_states

    def hasstate(self, window_name, object_name, state, guiTimeOut = 0):
        """
        has state

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string
        @type window_name: string
        @param state: State of the current object.
        @type object_name: string
        @param guiTimeOut: Wait timeout in seconds
        @type guiTimeOut: integer

        @return: 1 on success.
        @rtype: integer
        """
        try:
            object_handle=self._get_object_handle(window_name, object_name)
            if state == "enabled":
                return int(object_handle.AXEnabled)
            elif state == "focused":
                return int(object_handle.AXFocused)
            elif state == "focusable":
                return int(object_handle.AXFocused)
            elif state == "checked":
                if re.match("AXCheckBox", object_handle.AXRole,
                            re.M | re.U | re.L) or \
                            re.match("AXRadioButton", object_handle.AXRole,
                                     re.M | re.U | re.L):
                    if object_handle.AXValue:
                        return 1
        except:
            pass
        return 0

    def getobjectsize(self, window_name, object_name=None):
        """
        Get object size

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: x, y, width, height on success.
        @rtype: list
        """
        if not object_name:
            handle, name, app=self._get_window_handle(window_name)
        else:
            handle=self._get_object_handle(window_name, object_name)
        return self._getobjectsize(handle)

    def getwindowsize(self, window_name):
        """
        Get window size.

        @param window_name: Window name to get size of.
        @type window_name: string

        @return: list of dimensions [x, y, w, h]
        @rtype: list
        """
        return self.getobjectsize(window_name)

    def grabfocus(self, window_name, object_name=None):
        """
        Grab focus.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        if not object_name:
            handle, name, app=self._get_window_handle(window_name)
        else:
            handle=self._get_object_handle(window_name, object_name)
        return self._grabfocus(handle)

    def guiexist(self, window_name, object_name=None):
        """
        Checks whether a window or component exists.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        try:
            self._windows={}
            if not object_name:
                handle, name, app=self._get_window_handle(window_name, False)
            else:
                handle=self._get_object_handle(window_name, object_name,
                                               wait_for_object=False)
            # If window and/or object exist, exception will not be thrown
            # blindly return 1
            return 1
        except LdtpServerException:
            pass
        return 0

    def guitimeout(self, timeout):
      """
      Change GUI timeout period, default 30 seconds.

      @param timeout: timeout in seconds
      @type timeout: integer

      @return: 1 on success.
      @rtype: integer
      """
      self._window_timeout=timeout
      return 1

    def objtimeout(self, timeout):
      """
      Change object timeout period, default 5 seconds.

      @param timeout: timeout in seconds
      @type timeout: integer

      @return: 1 on success.
      @rtype: integer
      """
      self._obj_timeout=timeout
      return 1

    def waittillguiexist(self, window_name, object_name = '',
                         guiTimeOut = 30, state = ''):
        """
        Wait till a window or component exists.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string
        @param guiTimeOut: Wait timeout in seconds
        @type guiTimeOut: integer
        @param state: Object state used only when object_name is provided.
        @type object_name: string

        @return: 1 if GUI was found, 0 if not.
        @rtype: integer
        """
        timeout = 0
        while timeout < guiTimeOut:
            if self.guiexist(window_name, object_name):
                return 1
            # Wait 1 second before retrying
            time.sleep(1)
            timeout += 1
        # Object and/or window doesn't appear within the timeout period
        return 0

    def waittillguinotexist(self, window_name, object_name = '', guiTimeOut = 30):
        """
        Wait till a window does not exist.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string
        @param guiTimeOut: Wait timeout in seconds
        @type guiTimeOut: integer

        @return: 1 if GUI has gone away, 0 if not.
        @rtype: integer
        """
        timeout = 0
        while timeout < guiTimeOut:
            if not self.guiexist(window_name, object_name):
                return 1
            # Wait 1 second before retrying
            time.sleep(1)
            timeout += 1
        # Object and/or window still appears within the timeout period
        return 0

    def objectexist(self, window_name, object_name):
        """
        Checks whether a window or component exists.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string

        @return: 1 if GUI was found, 0 if not.
        @rtype: integer
        """
        try:
            object_handle=self._get_object_handle(window_name, object_name)
            return 1
        except LdtpServerException:
            return 0

    def stateenabled(self, window_name, object_name):
        """
        Check whether an object state is enabled or not

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string

        @return: 1 on success 0 on failure.
        @rtype: integer
        """
        try:
            object_handle=self._get_object_handle(window_name, object_name)
            if object_handle.AXEnabled:
                return 1
        except LdtpServerException:
            pass
        return 0

    def check(self, window_name, object_name):
        """
        Check item.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        # FIXME: Check for object type
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        if object_handle.AXValue == 1:
            # Already checked
            return 1
        # AXPress doesn't work with Instruments
        # So did the following work around
        self._grabfocus(object_handle)
        x, y, width, height=self._getobjectsize(object_handle)
        # Mouse left click on the object
        # Note: x + width/2, y + height / 2 doesn't work
        self.generatemouseevent(x + width / 2, y + height / 2, "b1c")
        return 1

    def uncheck(self, window_name, object_name):
        """
        Uncheck item.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        if object_handle.AXValue == 0:
            # Already unchecked
            return 1
        # AXPress doesn't work with Instruments
        # So did the following work around
        self._grabfocus(object_handle)
        x, y, width, height=self._getobjectsize(object_handle)
        # Mouse left click on the object
        # Note: x + width/2, y + height / 2 doesn't work
        self.generatemouseevent(x + width / 2, y + height / 2, "b1c")
        return 1

    def verifycheck(self, window_name, object_name):
        """
        Verify check item.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string

        @return: 1 on success 0 on failure.
        @rtype: integer
        """
        try:
            object_handle=self._get_object_handle(window_name, object_name,
                                                  wait_for_object=False)
            if object_handle.AXValue == 1:
                return 1
        except LdtpServerException:
            pass
        return 0

    def verifyuncheck(self, window_name, object_name):
        """
        Verify uncheck item.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string

        @return: 1 on success 0 on failure.
        @rtype: integer
        """
        try:
            object_handle=self._get_object_handle(window_name, object_name,
                                                  wait_for_object=False)
            if object_handle.AXValue == 0:
                return 1
        except LdtpServerException:
            pass
        return 0

    def getaccesskey(self, window_name, object_name):
        """
        Get access key of given object

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: access key in string format on success, else LdtpExecutionError on failure.
        @rtype: string
        """
        # Used http://www.danrodney.com/mac/ as reference for
        # mapping keys with specific control
        # In Mac noticed (in accessibility inspector) only menu had access keys
        # so, get the menu_handle of given object and
        # return the access key
        menu_handle=self._get_menu_handle(window_name, object_name)
        key=menu_handle.AXMenuItemCmdChar
        modifiers=menu_handle.AXMenuItemCmdModifiers
        glpyh=menu_handle.AXMenuItemCmdGlyph
        virtual_key=menu_handle.AXMenuItemCmdVirtualKey
        modifiers_type=""
        if modifiers == 0:
            modifiers_type="<command>"
        elif modifiers == 1:
            modifiers_type="<shift><command>"
        elif modifiers == 2:
            modifiers_type="<option><command>"
        elif modifiers == 3:
            modifiers_type="<option><shift><command>"
        elif modifiers == 4:
            modifiers_type="<ctrl><command>"
        elif modifiers == 6:
            modifiers_type="<ctrl><option><command>"
        # Scroll up
        if virtual_key==115 and glpyh==102:
            modifiers="<option>"
            key="<cursor_left>"
        # Scroll down
        elif virtual_key==119 and glpyh==105:
            modifiers="<option>"
            key="<right>"
        # Page up
        elif virtual_key==116 and glpyh==98:
            modifiers="<option>"
            key="<up>"
        # Page down
        elif virtual_key==121 and glpyh==107:
            modifiers="<option>"
            key="<down>"
        # Line up
        elif virtual_key==126 and glpyh==104:
            key="<up>"
        # Line down
        elif virtual_key==125 and glpyh==106:
            key="<down>"
        # Noticed in  Google Chrome navigating next tab
        elif virtual_key==124 and glpyh==101:
            key="<right>"
        # Noticed in  Google Chrome navigating previous tab
        elif virtual_key==123 and glpyh==100:
            key="<left>"
        # List application in a window to Force Quit
        elif virtual_key==53 and glpyh==27:
            key="<escape>"
        # FIXME:
        # * Instruments Menu View->Run Browser
        # modifiers==12 virtual_key==48 glpyh==2
        # * Terminal Menu Edit->Start Dictation
        # fn fn - glpyh==148 modifiers==24
        # * Menu Chrome->Clear Browsing Data in Google Chrome
        # virtual_key==51 glpyh==23 [Delete Left (like Backspace on a PC)]
        if not key:
            raise LdtpServerException("No access key associated")
        return modifiers_type + key
