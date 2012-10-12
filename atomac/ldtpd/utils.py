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

from constants import abbreviated_roles
from server_exception import LdtpServerException

class Utils(object):
    def __init__(self):
        self._appmap={}
        self._windows={}
        self._obj_timeout=5
        self._window_timeout=5
        # Current opened applications list will be updated
        self._running_apps=atomac.NativeUIElement._getRunningApps()
        if os.environ.has_key("LDTP_DEBUG"):
            self._ldtp_debug=True
        else:
            self._ldtp_debug=False

    def _get_front_most_window(self):
        front_app=atomac.NativeUIElement.getFrontmostApp()
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
            print actual_role
        return role, label

    def _insert_obj(self, obj_dict, obj):
        ldtpized_name=self._ldtpize_accessible(obj)
        try:
            key=u"%s%s" % (ldtpized_name[0], ldtpized_name[1])
        except UnicodeEncodeError:
            key=u"%s%s" % (ldtpized_name[0],
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
                key=u"%s%s%d" % (ldtpized_name[0],
                                   ldtpized_name[1], index)
            except UnicodeEncodeError:
                key=u"%s%s%d" % (ldtpized_name[0],
                                   ldtpized_name[1].decode("utf-8"), index)
            index += 1
        # FIXME: Change class to LDTP format ?
        # Get child_index, obj_index
        obj_dict[key]={"obj" : obj, "class" : self._get_role(obj),
                         "label" : ldtpized_name[1]}
        return key

    def _get_windows(self, force_remap=False):
        if not force_remap and self._windows:
            # Get the windows list from cache
            return self._windows
        # Update current running applications
        # as force_remap flag has been set
        self._update_apps()
        windows={}
        for gui in set(self._running_apps):
            # Get process id
            pid=gui.processIdentifier()
            # Get app id
            app=atomac.getAppRefByPid(pid)
            # Navigate all the windows
            for window in app.windows():
                if not window:
                    continue
                key=self._insert_obj(windows, window)
                windows[key]["app"]=app
        # Replace existing windows list
        self._windows=windows
        return windows

    def _get_title(self, obj):
        title=""
        try:
            checkBox=re.match("AXCheckBox", obj.AXRole, re.M | re.U | re.L)
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
                text=re.match("(AXTextField|AXTextArea)", obj.AXRole,
                                re.M | re.U | re.L)
                if text:
                    title=obj.AXFilename
                else:
                    if not re.match("(AXTabGroup)", obj.AXRole,
                                    re.M | re.U | re.L):
                        # Tab group has AXRadioButton as AXValue
                        # So skip it
                        if re.match("(AXScrollBar)", obj.AXRole,
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
                try:
                    if not re.match("(AXList|AXTable)", obj.AXRole,
                                    re.M | re.U | re.L):
                        # List have description as list
                        # So skip it
                        title=obj.AXRoleDescription
                except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
                    pass
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

    def _grabfocus(self, handle):
        if not handle:
            raise LdtpServerException("Invalid handle")
        handle.activate()
        return 1

    def _getobjectsize(self, handle):
        if not handle:
            raise LdtpServerException("Invalid handle")
        x, y=handle.AXPosition
        width, height=handle.AXSize
        return x, y, width, height

    def _get_window_handle(self, window_name, wait_for_window=True):
        window_obj=(None, None, None)
        if not window_name:
            raise LdtpServerException(u"Invalid argument passed to window_name")
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
            raise LdtpServerException(u"Unable to find window %s" % window_name)
        return window_obj

    def _get_object_handle(self, window_name, obj_name, obj_type=None,
                           wait_for_object=True):
        window_handle, ldtp_window_name, app=self._get_window_handle(window_name,
                                                                     wait_for_object)
        if not window_handle or not window_name:
            raise LdtpServerException(u"Unable to find window %s" % window_name)
        strip=r"( |:|\.|_|\n)"
        if not isinstance(obj_name, unicode):
            # Convert to unicode string
            obj_name=u"%s" % obj_name
        stripped_obj_name=re.sub(strip, u"", obj_name)
        obj_name=fnmatch.translate(obj_name)
        stripped_obj_name=fnmatch.translate(stripped_obj_name)
        object_list=self._get_appmap(window_handle, ldtp_window_name)
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
                    # Return object handle
                    # FIXME: Check object validity before returning
                    # if object state is invalid, then remap
                    return object_list[obj]["obj"]
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
            # print object_list
        raise LdtpServerException(u"Unable to find object %s" % obj_name)

    def _get_appmap(self, window_handle, window_name, force_remap=False):
        if not window_handle or not window_name:
            # If invalid argument return empty dict
            return {}
        if not force_remap and self._appmap.has_key(window_name):
            # If available in cache then use that
            # unless remap is forced
            return self._appmap[window_name]
        obj_dict={}
        # Populate the appmap and cache it
        for obj in window_handle.findAllR():
            self._insert_obj(obj_dict, obj)
        # Cache the object dictionary
        self._appmap[window_name]=obj_dict
        return obj_dict

    def _get_menu_handle(self, window_name, object_name,
                         wait_for_window=True):
        window_handle, name, app=self._get_window_handle(window_name,
                                                           wait_for_window)
        if not window_handle:
            raise LdtpServerException(u"Unable to find window %s" % window_name)
        # pyatom doesn't understand LDTP convention mnu, strip it off
        menu_handle=app.menuItem(re.sub("mnu", "", object_name))
        if not menu_handle:
            raise LdtpServerException(u"Unable to find menu %s" % object_name)
        return menu_handle

    def _get_sub_menu_handle(self, children, menu):
        strip=r"( |:|\.|_|\n)"
        tmp_menu=fnmatch.translate(menu)
        stripped_menu=fnmatch.translate(re.sub(strip, u"", menu))
        for current_menu in children.AXChildren:
            role, label=self._ldtpize_accessible(current_menu)
            x, y, width, height=self._getobjectsize(current_menu)
            if re.match(tmp_menu, label) or \
                    re.match(tmp_menu, u"%s%s" % (role, label)) or \
                    re.match(stripped_menu, label) or \
                    re.match(stripped_menu, u"%s%s" % (role, label)):
                return current_menu
        raise LdtpServerException(u"Unable to find menu %s" % menu)

    def _internal_menu_handler(self, menu_handle, menu_list,
                               perform_action = False):
        if not menu_handle or not menu_list:
            raise LdtpServerException(u"Unable to find menu %s" % [0])
        for menu in menu_list:
            # Get AXMenu
            children=menu_handle.AXChildren[0]
            if not children:
                raise LdtpServerException(u"Unable to find menu %s" % menu)
            menu_handle=self._get_sub_menu_handle(children, menu)
            # Don't perform action on last item
            if perform_action and menu_list[-1] != menu:
                if not menu_handle.AXEnabled:
                    # click back on combo box
                    menu_handle.Cancel()
                    raise LdtpServerException(u"Object %s state disabled" % \
                                              menu)
                    # Click current menuitem, required for combo box
                    menu_handle.Press()
                    # Required for menuitem to appear in accessibility list
                    self.wait(1) 
            if not menu_handle:
                raise LdtpServerException(u"Unable to find menu %s" % menu)
        return menu_handle
