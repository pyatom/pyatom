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

from utils import Utils

class Core(Utils):
    def __init__(self):
        Utils.__init__(self)

    """Core LDTP class"""
    def getapplist(self):
        """
        Get all currently running application names

        @return: list of unicode application names
        @rtype: list
        """
        app_list = []
        for gui in self.running_apps:
            app_list.append(gui.localizedName())
        # Return unique application list
        return list(set(app_list))

    def getobjectlist(self, windowName):
        if not windowName:
            return []
        objectList = {}
        windowHandle = self._getwindowhandle(windowName)
        currentWindowName = self._getwindowtitle(windowHandle)
        for obj in windowHandle.findAllR():
            try:
                key = u"%s%s" % (self._getrole(obj), self._getvalue(obj))
            except UnicodeEncodeError:
                key = u"%s%s" % (self._getrole(obj), self._getvalue(obj).decode('utf-8'))
            objectList[key] = obj
        return objectList

    def getwindowlist(self):
        windowList = []
        # Navigate all the windows
        for window in self._getwindows():
            if not window:
                continue
            title = self._getwindowtitle(window)
            role = self._getrole(window)
            #print window.getAttributes(), title, role
            if title:
                windowList.append(title)
        return windowList

if __name__ == "__main__":
    test = Core()
    print test.getapplist()
    print test.getwindowlist()
    print test.getobjectlist("*Contacts*")
