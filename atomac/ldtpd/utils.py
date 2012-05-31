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
"""Core class to be exposed via XMLRPC in LDTP daemon."""

import re
import atomac
import fnmatch

class Utils(object):
    def __init__(self):
        # FIXME: Currently this is not updated at run-time
        # Current opened applications list will be returned
        self.running_apps = atomac.NativeUIElement._getApps()

    def _getwindows(self):
        windows = []
        for gui in set(self.running_apps):
            # Get process id
            pid = gui.processIdentifier()
            # Get app id
            app = atomac.getAppRefByPid(pid)
            # Navigate all the windows
            for window in app.windows():
                if not window:
                    continue
                windows.append(window)
        return windows

    def _getvalue(self, obj):
        value = None
        try:
            value=obj.AXValue
        except atomac._a11y.ErrorUnsupported:
            try:
                value=obj.AXRoleDescription
            except atomac._a11y.ErrorUnsupported:
                pass
        return value

    def _getwindowtitle(self, window):
        title = ''
        try:
            title=window.AXTitle
        except atomac._a11y.ErrorUnsupported:
            try:
                title=window.AXValue
            except atomac._a11y.ErrorUnsupported:
                try:
                    title=window.AXRoleDescription
                except atomac._a11y.ErrorUnsupported:
                    pass
        return title

    def _getrole(self, obj):
        role = ''
        try:
            role=obj.AXRole
        except atomac._a11y.ErrorUnsupported:
            pass
        return role

    def _getwindowhandle(self, windowName):
        if not windowName:
            return None
        windowName = fnmatch.translate(windowName)
        for window in set(self._getwindows()):
            currentWindowName = self._getwindowtitle(window)
            #print currentWindowName, windowName
            if currentWindowName and re.match(windowName, currentWindowName):
                return window
        return None
