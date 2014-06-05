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
"""Utils class."""

import os
import re
import time
import atomac
import fnmatch
import logging
import threading
import traceback
import logging.handlers

from constants import abbreviated_roles, ldtp_class_type
from server_exception import LdtpServerException

importPsUtil = False
try:
    import psutil
    importPsUtil=True
except ImportError:
    pass

class LdtpCustomLog(logging.Handler):
    """
    Custom LDTP log, inherit logging.Handler and implement
    required API
    """
    def __init__(self):
        # Call base handler
        logging.Handler.__init__(self)
        # Log all the events in list
        self.log_events=[]

    def emit(self, record):
        # Get the message and add to the list
        # Later the list element can be poped out
        self.log_events.append(u'%s-%s' % (record.levelname, record.getMessage()))

# Add LdtpCustomLog handler
logging.handlers.LdtpCustomLog=LdtpCustomLog
# Create instance of LdtpCustomLog handler
_custom_logger=logging.handlers.LdtpCustomLog()
# Set default log level as ERROR
_custom_logger.setLevel(logging.ERROR)
# Add handler to root logger
logger=logging.getLogger('')
# Add custom logger to the root logger
logger.addHandler(_custom_logger)

LDTP_LOG_MEMINFO=60
LDTP_LOG_CPUINFO=61
logging.addLevelName(LDTP_LOG_MEMINFO, 'MEMINFO')
logging.addLevelName(LDTP_LOG_CPUINFO, 'CPUINFO')

class ProcessStats(threading.Thread):
    """
    Capturing Memory and CPU Utilization statistics for an application and its related processes
    NOTE: You have to install python-psutil package
    EXAMPLE USAGE:

    xstats = ProcessStats('evolution', 2)
    # Start Logging by calling start
    xstats.start()
    # Stop the process statistics gathering thread by calling the stopstats method
    xstats.stop()
    """

    def __init__(self, appname, interval = 2):
        """
        Start memory and CPU monitoring, with the time interval between
        each process scan

        @param appname: Process name, ex: firefox-bin.
        @type appname: string
        @param interval: Time interval between each process scan
        @type interval: float
        """
        if not importPsUtil:
            raise LdtpServerException('python-psutil package is not installed')
        threading.Thread.__init__(self)
        self._appname = appname
        self._interval = interval
        self._stop = False
        self.running = True

    def __del__(self):
        self._stop = False
        self.running = False

    def get_cpu_memory_stat(self):
        proc_list = []
        for p in psutil.process_iter():
            if self._stop:
                self.running = False
                return proc_list
            if not re.match(fnmatch.translate(self._appname),
                            p.name, re.U | re.L):
                # If process name doesn't match, continue
                continue
            proc_list.append(p)
        return proc_list

    def run(self):
        while not self._stop:
            for p in self.get_cpu_memory_stat():
                try:
                    # Add the stats into ldtp log
                    # Resident memory will be in bytes, to convert it to MB
                    # divide it by 1024*1024
                    logger.log(LDTP_LOG_MEMINFO, '%s(%s) - %s' % \
                                   (p.name, str(p.pid), p.get_memory_percent()))
                    # CPU percent returned with 14 decimal values
                    # ex: 0.0281199122531, round it to 2 decimal values
                    # as 0.03
                    logger.log(LDTP_LOG_CPUINFO, '%s(%s) - %s' % \
                                   (p.name, str(p.pid), p.get_cpu_percent()))
                except psutil.AccessDenied:
                    pass
            # Wait for interval seconds before gathering stats again
            try:
                time.sleep(self._interval)
            except KeyboardInterrupt:
                self._stop = True

    def stop(self):
        self._stop = True
        self.running = False

class Utils(object):
    def __init__(self):
        self._appmap={}
        self._windows={}
        self._obj_timeout=5
        self._window_timeout=30
        self._callback_event=[]
        self._app_under_test=None
        self._custom_logger=_custom_logger
        # Current opened applications list will be updated
        self._running_apps=atomac.NativeUIElement._getRunningApps()
        if os.environ.has_key("LDTP_DEBUG"):
            self._ldtp_debug=True
            self._custom_logger.setLevel(logging.DEBUG)
        else:
            self._ldtp_debug=False
        self._ldtp_debug_file = os.environ.get('LDTP_DEBUG_FILE', None)

    def _listMethods(self):
        _methods=[]
        for symbol in dir(self):
            if symbol.startswith('_'): 
                continue
            _methods.append(symbol)
        return _methods

    def _methodHelp(self, method):
        return getattr(self, method).__doc__

    def _dispatch(self, method, args):
        try:
            return getattr(self, method)(*args)
        except:
            if self._ldtp_debug:
                print(traceback.format_exc())
            if self._ldtp_debug_file:
                with open(self._ldtp_debug_file, "a") as fp:
                    fp.write(traceback.format_exc())
            raise

    def _get_front_most_window(self):
        app=atomac.NativeUIElement.getFrontmostApp()
        return app.windows()[0]

    def _get_any_window(self):
        front_app=atomac.NativeUIElement.getAnyAppWithWindow()
        return front_app.windows()[0]

    def _ldtpize_accessible(self, acc):
        """
        Get LDTP format accessibile name

        @param acc: Accessible handle
        @type acc: object

        @return: object type, stripped object name (associated / direct),
                        associated label
        @rtype: tuple
        """
        actual_role=self._get_role(acc)
        label=self._get_title(acc)
        if re.match("AXWindow", actual_role, re.M | re.U | re.L):
            # Strip space and new line from window title
            strip=r"( |\n)"
        else:
            # Strip space, colon, dot, underscore and new line from
            # all other object types
            strip=r"( |:|\.|_|\n)"
        if label:
            # Return the role type (if, not in the know list of roles,
            # return ukn - unknown), strip the above characters from name
            # also return labely_by string
            if not isinstance(label, unicode):
                label=u"%s" % label
            label=re.sub(strip, u"", label)
        role=abbreviated_roles.get(actual_role, "ukn")
        if self._ldtp_debug and role == "ukn":
            print(actual_role, acc)
        return role, label

    def _glob_match(self, pattern, string):
        """
        Match given string, by escaping regex characters
        """
        # regex flags Multi-line, Unicode, Locale
        return bool(re.match(fnmatch.translate(pattern), string,
                             re.M | re.U | re.L))
 
    def _match_name_to_appmap(self, name, acc):
        if not name:
            return 0
        if self._glob_match(name, acc['obj_index']):
            return 1
        if self._glob_match(name, acc['label']):
            return 1
        role = acc['class']
        if role == 'frame' or role == 'dialog' or role == 'window':
            strip = '( |\n)'
        else:
            strip = '( |:|\.|_|\n)'
        obj_name = re.sub(strip, '', name)
        if acc['label']:
            _tmp_name = re.sub(strip, '', acc['label'])
            if self._glob_match(obj_name, _tmp_name):
                return 1
        return 0

    def _insert_obj(self, obj_dict, obj, parent, child_index):
        ldtpized_name=self._ldtpize_accessible(obj)
        if ldtpized_name[0] in self._ldtpized_obj_index:
            self._ldtpized_obj_index[ldtpized_name[0]] += 1
        else:
            self._ldtpized_obj_index[ldtpized_name[0]]=0
        try:
            key="%s%s" % (ldtpized_name[0], ldtpized_name[1])
        except UnicodeEncodeError:
            key="%s%s" % (ldtpized_name[0],
                          ldtpized_name[1].decode("utf-8"))
        if not ldtpized_name[1]:
            index=0
            # Object doesn't have any associated label
            key="%s%d" % (ldtpized_name[0], index)
        else:
            index=1
        while obj_dict.has_key(key):
            # If the same object type with matching label exist
            # add index to it
            try:
                key="%s%s%d" % (ldtpized_name[0],
                                ldtpized_name[1], index)
            except UnicodeEncodeError:
                key="%s%s%d" % (ldtpized_name[0],
                                ldtpized_name[1].decode("utf-8"), index)
            index += 1
        if ldtpized_name[0] == "frm":
            # Window
            # FIXME: As in Linux (app#index, rather than window#index)
            obj_index="%s#%d" % (ldtpized_name[0],
                                 self._ldtpized_obj_index[ldtpized_name[0]])
        else:
            # Object inside the window
            obj_index="%s#%d" % (ldtpized_name[0],
                                 self._ldtpized_obj_index[ldtpized_name[0]])
        if parent in obj_dict:
            _current_children=obj_dict[parent]["children"]
            if _current_children:
                _current_children="%s %s" % (_current_children, key)
            else:
                _current_children=key
            obj_dict[parent]["children"]=_current_children
        actual_role=self._get_role(obj)
        obj_dict[key]={"obj" : obj,
                       # Use Linux based class type for compatibility
                       # If class type doesn't exist in list, use actual type
                       "class" : ldtp_class_type.get(actual_role, actual_role),
                       "label" : ldtpized_name[1],
                       "parent" : parent,
                       "children" : "",
                       "child_index" : child_index,
                       "obj_index" : obj_index}
        return key

    def _get_windows(self, force_remap=False):
        if not force_remap and self._windows:
            # Get the windows list from cache
            return self._windows
        # Update current running applications
        # as force_remap flag has been set
        self._update_apps()
        windows={}
        self._ldtpized_obj_index={}
        for gui in set(self._running_apps):
            if self._app_under_test and \
                    self._app_under_test != gui.bundleIdentifier() and \
                    self._app_under_test != gui.localizedName():
                # Not the app under test, search next application
                continue
            # Get process id
            pid=gui.processIdentifier()
            # Get app id
            app=atomac.getAppRefByPid(pid)
            # Get all windows of current app
            app_windows=app.windows()
            try:
                # Tested with
                # selectmenuitem('appChickenoftheVNC', 'Connection;Open Connection...')
                if not app_windows and app.AXRole == "AXApplication":
                    # If app doesn't have any windows and its role is AXApplication
                    # add to window list
                    key=self._insert_obj(windows, app, "", -1)
                    windows[key]["app"]=app
                    continue
            except (atomac._a11y.ErrorAPIDisabled, \
                        atomac._a11y.ErrorCannotComplete, \
                        atomac._a11y.Error, \
                        atomac._a11y.ErrorInvalidUIElement):
                pass
            # Navigate all the windows
            for window in app_windows:
                if not window:
                    continue
                key=self._insert_obj(windows, window, "", -1)
                windows[key]["app"]=app
        # Replace existing windows list
        self._windows=windows
        return windows

    def _get_title(self, obj):
        title=""
        role=""
        try:
            role=obj.AXRole
            desc=obj.AXRoleDescription
            if re.match("(AXStaticText|AXRadioButton|AXButton)",
                        role, re.M | re.U | re.L) and \
                    (desc == "text" or desc == "radio button" or \
                         desc == "button") and obj.AXValue:
                return obj.AXValue
        except:
            pass
        try:
            checkBox=re.match("AXCheckBox", role, re.M | re.U | re.L)
            if checkBox:
                # Instruments doesn't have AXTitle, AXValue for AXCheckBox
                try:
                    title=obj.AXHelp
                except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
                    pass
            if not title:
                title=obj.AXTitle
        except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
            try:
                text=re.match("(AXTextField|AXTextArea)", role,
                                re.M | re.U | re.L)
                if text:
                    title=obj.AXFilename
                else:
                    if not re.match("(AXTabGroup)", role,
                                    re.M | re.U | re.L):
                        # Tab group has AXRadioButton as AXValue
                        # So skip it
                        if re.match("(AXScrollBar)", role,
                                    re.M | re.U | re.L):
                            # ScrollBar value is between 0 to 1
                            # which is used to get the current location
                            # of the ScrollBar, rather than the object name
                            # Let us have the title as empty string and
                            # refer the ScrollBar as scbr0 (Vertical),
                            # scbr1 (Horizontal)
                            title=""
                        else:
                            title=obj.AXValue
            except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
                if re.match("AXButton", role,
                            re.M | re.U | re.L):
                    try:
                        title=obj.AXDescription
                        if title:
                            return title
                    except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
                        pass
                try:
                    if not re.match("(AXList|AXTable)", role,
                                    re.M | re.U | re.L):
                        # List have description as list
                        # So skip it
                        title=obj.AXRoleDescription
                except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
                    pass
        if not title:
            if re.match("(AXButton|AXCheckBox)", role,
                        re.M | re.U | re.L):
                try:
                    title=obj.AXRoleDescription
                    if title:
                       return title
                except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
                    pass
            elif re.match("(AXStaticText)", role,
                          re.M | re.U | re.L):
                try:
                    title=obj.AXValue
                    if title:
                       return title
                except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
                    pass
            # Noticed that some of the above one assigns title as None
            # in that case return empty string
            return ""
        return title

    def _get_role(self, obj):
        role=""
        try:
            role=obj.AXRole
        except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
            pass
        return role

    def _update_apps(self):
        # Current opened applications list will be updated
        self._running_apps=atomac.NativeUIElement._getRunningApps()

    def _singleclick(self, window_name, object_name):
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        size=self._getobjectsize(object_handle)
        self._grabfocus(object_handle)
        self.wait(0.5)
        self.generatemouseevent(size[0] + size[2]/2, size[1] + size[3]/2, "b1c")
        return 1

    def _grabfocus(self, handle):
        if not handle:
            raise LdtpServerException("Invalid handle")
        
        try:
            if handle.AXRole == "AXWindow":
                # Raise window
                handle.Raise()
        except (AttributeError,):
            try:
                if handle[0].AXRole == "AXWindow":
                    handle[0].Raise()
            except (IndexError, AttributeError):
                # First bring the window to front
                handle.AXWindow.Raise()
                # Focus object
                handle.activate()
        return 1

    def _getobjectsize(self, handle):
        if not handle:
            raise LdtpServerException("Invalid handle")
        x, y=handle.AXPosition
        width, height=handle.AXSize
        return x, y, width, height

    def _get_window_handle(self, window_name, wait_for_window=True):
        if not window_name:
            raise LdtpServerException("Invalid argument passed to window_name")
        # Will be used to raise the exception with user passed window name
        orig_window_name=window_name
        window_obj=(None, None, None)
        strip=r"( |\n)"
        if not isinstance(window_name, unicode):
            # Convert to unicode string
            window_name=u"%s" % window_name
        stripped_window_name=re.sub(strip, u"", window_name)
        window_name=fnmatch.translate(window_name)
        stripped_window_name=fnmatch.translate(stripped_window_name)
        windows=self._get_windows()
        def _internal_get_window_handle(windows):
            # To handle retry this function has been introduced
            for window in windows:
                label=windows[window]["label"]
                strip=r"( |\n)"
                if not isinstance(label, unicode):
                    # Convert to unicode string
                    label=u"%s" % label
                stripped_label=re.sub(strip, u"", label)
                # FIXME: Find window name in LDTP format 
                if re.match(window_name, window) or \
                        re.match(window_name, label) or \
                        re.match(window_name, stripped_label) or \
                        re.match(stripped_window_name, window) or \
                        re.match(stripped_window_name, label) or \
                        re.match(stripped_window_name, stripped_label):
                    # Return window handle and window name
                    return (windows[window]["obj"], window, windows[window]["app"])
            return (None, None, None)
        if wait_for_window:
            window_timeout=self._obj_timeout
        else:
            # don't wait for the window 
            window_timeout=1
        for retry in range(0, window_timeout):
            window_obj=_internal_get_window_handle(windows)
            if window_obj[0]:
                # If window object found, return immediately
                return window_obj
            if window_timeout <= 1:
                # Don't wait for the window
                break
            time.sleep(1)
            windows=self._get_windows(True)
        if not window_obj[0]:
            raise LdtpServerException('Unable to find window "%s"' % \
                                          orig_window_name)
        return window_obj

    def _get_object_handle(self, window_name, obj_name, obj_type=None,
                           wait_for_object=True):
        try:
            return self._internal_get_object_handle(window_name, obj_name,
                                                    obj_type, wait_for_object)
        except atomac._a11y.ErrorInvalidUIElement:
            # During the test, when the window closed and reopened
            # ErrorInvalidUIElement exception will be thrown
            self._windows={}
            # Call the method again, after updating apps
            return self._internal_get_object_handle(window_name, obj_name,
                                                    obj_type, wait_for_object)

    def _internal_get_object_handle(self, window_name, obj_name, obj_type=None,
                                    wait_for_object=True):
        try:
            obj=self._get_object_map(window_name, obj_name, obj_type,
                                     wait_for_object)
            # Object might not exist, just check whether it exist
            object_handle=obj["obj"]
            # Look for Window's role, on stale windows this will
            # throw AttributeError exception, if so relookup windows
            # and search for the object
            object_handle.AXWindow.AXRole
        except (atomac._a11y.ErrorCannotComplete,
                atomac._a11y.ErrorUnsupported,
                atomac._a11y.ErrorInvalidUIElement, AttributeError):
            # During the test, when the window closed and reopened
            # ErrorCannotComplete exception will be thrown
            self._windows={}
            # Call the method again, after updating apps
            obj=self._get_object_map(window_name, obj_name, obj_type,
                                     wait_for_object, True)
        # Return object handle
        # FIXME: Check object validity before returning
        # if object state is invalid, then remap
        return obj["obj"]

    def _get_object_map(self, window_name, obj_name, obj_type=None,
                           wait_for_object=True, force_remap=False):
        if not window_name:
            raise LdtpServerException("Unable to find window %s" % window_name)
        window_handle, ldtp_window_name, app=self._get_window_handle(window_name,
                                                                     wait_for_object)
        if not window_handle:
            raise LdtpServerException("Unable to find window %s" % window_name)
        strip=r"( |:|\.|_|\n)"
        if not isinstance(obj_name, unicode):
            # Convert to unicode string
            obj_name=u"%s" % obj_name
        stripped_obj_name=re.sub(strip, u"", obj_name)
        obj_name=fnmatch.translate(obj_name)
        stripped_obj_name=fnmatch.translate(stripped_obj_name)
        object_list=self._get_appmap(window_handle, ldtp_window_name, force_remap)
        def _internal_get_object_handle(object_list):
            # To handle retry this function has been introduced
            for obj in object_list:
                if obj_type and object_list[obj]["class"] != obj_type:
                    # If object type is provided and doesn't match
                    # don't proceed further, just continue searching
                    # next element, even though the label matches
                    continue
                label=object_list[obj]["label"]
                strip=r"( |:|\.|_|\n)"
                if not isinstance(label, unicode):
                    # Convert to unicode string
                    label=u"%s" % label
                stripped_label=re.sub(strip, u"", label)
                # FIXME: Find object name in LDTP format
                if re.match(obj_name, obj) or re.match(obj_name, label) or \
                        re.match(obj_name, stripped_label) or \
                        re.match(stripped_obj_name, obj) or \
                        re.match(stripped_obj_name, label) or \
                        re.match(stripped_obj_name, stripped_label):
                    # Return object map
                    return object_list[obj]
        if wait_for_object:
            obj_timeout=self._obj_timeout
        else:
            # don't wait for the object 
            obj_timeout=1
        for retry in range(0, obj_timeout):
            obj=_internal_get_object_handle(object_list)
            if obj:
                # If object found, return immediately
                return obj
            if obj_timeout <= 1:
                # Don't wait for the object
                break
            time.sleep(1)
            # Force remap
            object_list=self._get_appmap(window_handle,
                                         ldtp_window_name, True)
            # print(object_list)
        raise LdtpServerException("Unable to find object %s" % obj_name)

    def _populate_appmap(self, obj_dict, obj, parent, child_index):
        index=-1
        if obj:
            if child_index != -1:
                parent=self._insert_obj(obj_dict, obj, parent, child_index)
            try:
                if not obj.AXChildren:
                    return
            except atomac._a11y.Error:
                return
            for child in obj.AXChildren:
                index += 1
                if not child:
                    continue
                self._populate_appmap(obj_dict, child, parent, index)

    def _get_appmap(self, window_handle, window_name, force_remap=False):
        if not window_handle or not window_name:
            # If invalid argument return empty dict
            return {}
        if not force_remap and self._appmap.has_key(window_name):
            # If available in cache then use that
            # unless remap is forced
            return self._appmap[window_name]
        obj_dict={}
        self._ldtpized_obj_index={}
        # Populate the appmap and cache it
        self._populate_appmap(obj_dict, window_handle, "", -1)
        # Cache the object dictionary
        self._appmap[window_name]=obj_dict
        return obj_dict

    def _get_menu_handle(self, window_name, object_name,
                         wait_for_window=True):
        window_handle, name, app=self._get_window_handle(window_name,
                                                         wait_for_window)
        if not window_handle:
            raise LdtpServerException("Unable to find window %s" % window_name)
        # pyatom doesn't understand LDTP convention mnu, strip it off
        menu=re.sub("mnu", "", object_name)
        if re.match("^\d", menu):
            obj_dict=self._get_appmap(window_handle, name)
            return obj_dict[object_name]["obj"]
        menu_handle=app.menuItem(menu)
        if  menu_handle:
            return menu_handle
        # Above one looks for menubar item
        # Following looks for menuitem inside the window
        menu_handle_list=window_handle.findAllR(AXRole="AXMenu")
        for menu_handle in menu_handle_list:
            sub_menu_handle=self._get_sub_menu_handle(menu_handle, object_name)
            if sub_menu_handle:
                return sub_menu_handle
        raise LdtpServerException("Unable to find menu %s" % object_name)

    def _get_sub_menu_handle(self, children, menu):
        strip=r"( |:|\.|_|\n)"
        tmp_menu=fnmatch.translate(menu)
        stripped_menu=fnmatch.translate(re.sub(strip, u"", menu))
        for current_menu in children.AXChildren:
            role, label=self._ldtpize_accessible(current_menu)
            if re.match(tmp_menu, label) or \
                    re.match(tmp_menu, u"%s%s" % (role, label)) or \
                    re.match(stripped_menu, label) or \
                    re.match(stripped_menu, u"%s%s" % (role, label)):
                return current_menu
        raise LdtpServerException("Unable to find menu %s" % menu)

    def _internal_menu_handler(self, menu_handle, menu_list,
                               perform_action = False):
        if not menu_handle or not menu_list:
            raise LdtpServerException("Unable to find menu %s" % [0])
        for menu in menu_list:
            # Get AXMenu
            if not menu_handle.AXChildren:
                try:
                    # Noticed this issue, on clicking Skype
                    # menu in notification area
                    menu_handle.Press()
                except atomac._a11y.ErrorCannotComplete:
                    if self._ldtp_debug:
                        print traceback.format_exc()
                    if self._ldtp_debug_file:
                        with open(self._ldtp_debug_file, "a") as fp:
                            fp.write(traceback.format_exc())
            # For some reason, on accessing the lenght first
            # doesn't crash, else
            """
            Traceback (most recent call last):
              File "build/bdist.macosx-10.8-intel/egg/atomac/ldtpd/utils.py", line 178, in _dispatch
                return getattr(self, method)(*args)
              File "build/bdist.macosx-10.8-intel/egg/atomac/ldtpd/menu.py", line 63, in selectmenuitem
                menu_handle=self._get_menu_handle(window_name, object_name)
              File "build/bdist.macosx-10.8-intel/egg/atomac/ldtpd/menu.py", line 47, in _get_menu_handle
                return self._internal_menu_handler(menu_handle, menu_list[1:])
              File "build/bdist.macosx-10.8-intel/egg/atomac/ldtpd/utils.py", line 703, in _internal_menu_handler
                children=menu_handle.AXChildren[0]
            IndexError: list index out of range
            """
            len(menu_handle.AXChildren)
            # Now with above line, everything works fine
            # on doing selectmenuitem('appSystemUIServer', 'mnu0;Open Display*')
            children=menu_handle.AXChildren[0]
            if not children:
                raise LdtpServerException("Unable to find menu %s" % menu)
            menu_handle=self._get_sub_menu_handle(children, menu)
            # Don't perform action on last item
            if perform_action and menu_list[-1] != menu:
                if not menu_handle.AXEnabled:
                    # click back on combo box
                    menu_handle.Cancel()
                    raise LdtpServerException("Object %s state disabled" % \
                                              menu)
                    # Click current menuitem, required for combo box
                    menu_handle.Press()
                    # Required for menuitem to appear in accessibility list
                    self.wait(1) 
            if not menu_handle:
                raise LdtpServerException("Unable to find menu %s" % menu)
        return menu_handle

    def _getfirstmatchingchild(self, obj, role):
        if not obj or not role:
            return
        if re.match(role, obj.AXRole):
            return obj
        if  not obj.AXChildren:
            return
        for child in obj.AXChildren:
            matching_child = self._getfirstmatchingchild(child, role)
            if matching_child:
                return matching_child
        return
