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
import atomac.AXClasses as AXClasses

class Ldtpd(object):
    def __init__(self):
        self.uiElement = AXClasses.NativeUIElement()

    """Core LDTP class"""
    def getapplist(self):
        """
        Get all currently running application names

        @return: list of unicode application names
        @rtype: list
        """
        app_list = []
        for gui in self.uiElement._getApps():
            app_list.append(gui.localizedName())
        # Return unique application list
        return list(set(app_list))

    def _getwindows(self):
        windows = []
        for gui in set(self.uiElement._getApps()):
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
        except Exception:
            try:
                value=obj.AXRoleDescription
            except Exception:
                pass
        return value

    def _getwindowtitle(self, window):
        title = None
        try:
            title=window.AXTitle
        except Exception:
            try:
                title=window.AXValue
            except Exception:
                try:
                    title=window.AXRoleDescription
                except Exception:
                    pass
        return title

    def _getrole(self, obj):
        role = None
        try:
            role=obj.AXRole
        except Exception:
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

    def getobjectlist(self, windowName):
        if not windowName:
            return []
        objectList = {}
        windowHandle = self._getwindowhandle(windowName)
        currentWindowName = self._getwindowtitle(windowHandle)
        for obj in windowHandle.findAllR():
            key = self._getrole(obj) + str(self._getvalue(obj))
            objectList[key] = obj
        return objectList

    def getwindowlist(self):
        windowList = []
        # Navigate all the windows
        for window in self._getwindows():
            if not window:
                continue
            title = self._getwindowtitle(window)
            role = self._getwindowrole(window)
            #print window.getAttributes(), title, role
            if title:
                windowList.append(title)
        return windowList

if __name__ == "__main__":
    test = Ldtpd()
    #print test.getapplist()
    #print test.getwindowlist()
    print test.getobjectlist("*Contacts*")
