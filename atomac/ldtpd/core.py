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
import time
import atomac
import fnmatch

from utils import Utils
from combo_box import ComboBox
from server_exception import LdtpServerException

class Core(Utils, ComboBox):
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
        for gui in self._running_apps:
            app_list.append(gui.localizedName())
        # Return unique application list
        return list(set(app_list))

    def getwindowlist(self):
        return self._get_windows().keys()

    def getobjectlist(self, window_name):
        if not window_name:
            return {}
        window_handle, window_name = self._get_window_handle(window_name)
        if not window_handle:
            return {}
        object_list = self._get_appmap(window_handle, window_name)
        return object_list.keys()

    def wait(self, timeout = 5):
        time.sleep(timeout)
        return 1

    def click(self, window_name, object_name):
        object_handle = self._get_object_handle(window_name, object_name)
        if not object_handle:
            raise LdtpServerException(u"Unable to find object %s" % object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        object_handle.Press()
        return 1

    def getobjectsize(self, window_name, object_name = None):
        if not object_name: 
            window_handle, window_name = self._get_window_handle(window_name)
            if not window_handle:
                raise LdtpServerException(u"Unable to find window %s" % object_name)
            x, y = window_handle.AXPosition
            width, height = window_handle.AXSize
        else:
            object_handle = self._get_object_handle(window_name, object_name)
            if not object_handle:
                raise LdtpServerException(u"Unable to find object %s" % object_name)
            x, y = object_handle.AXPosition
            width, height = object_handle.AXSize
        return x, y, width, height

    def getwindowsize(self, window_name):
        return self.getobjectsize(window_name)

    def grabfocus(self, window_name, object_name = None):
        if not object_name: 
            window_handle, window_name = self._get_window_handle(window_name)
            if not window_handle:
                raise LdtpServerException(u"Unable to find window %s" % object_name)
            window_handle.AXWindow.Raise()
        else:
            object_handle = self._get_object_handle(window_name, object_name)
            if not object_handle:
                raise LdtpServerException(u"Unable to find object %s" % object_name)
            object_handle.AXWindow.Raise()
        return 1

    def check(self, window_name, object_name):
        # FIXME: Check for object type
        object_handle = self._get_object_handle(window_name, object_name)
        if not object_handle:
            raise LdtpServerException(u"Unable to find object %s" % object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        if object_handle.AXValue == 1:
            # Already checked
            return 1
        # AXPress doesn't work with Instruments
        # So did the following work around
        self.grabfocus(window_name, object_name)
        x, y, width, height = self.getobjectsize(window_name, object_name)
        # Mouse left click on the object
        # Note: x + width/2, y + height / 2 doesn't work
        object_handle.clickMouseButtonLeft((x + width / 2, y + height / 2))
        return 1

    def uncheck(self, window_name, object_name):
        object_handle = self._get_object_handle(window_name, object_name)
        if not object_handle:
            raise LdtpServerException(u"Unable to find object %s" % object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        if object_handle.AXValue == 0:
            # Already unchecked
            return 1
        # AXPress doesn't work with Instruments
        # So did the following work around
        self.grabfocus(window_name, object_name)
        x, y, width, height = self.getobjectsize(window_name, object_name)
        # Mouse left click on the object
        # Note: x + width/2, y + height / 2 doesn't work
        object_handle.clickMouseButtonLeft((x + width / 2, y + height / 2))
        return 1

    def verifycheck(self, window_name, object_name):
        object_handle = self._get_object_handle(window_name, object_name,
                                                wait_for_object = False)
        if not object_handle:
            return 0
        if object_handle.AXValue == 1:
            return 1
        return 0

    def verifyuncheck(self, window_name, object_name):
        object_handle = self._get_object_handle(window_name, object_name,
                                                wait_for_object = False)
        if not object_handle:
            return 0
        if object_handle.AXValue == 0:
            return 1
        return 0

if __name__ == "__main__":
    test = Core()
    #print test.getapplist()
    #print test.getwindowlist()
    #print test.getobjectlist("Contacts")
    #print test.click("Open", "Cancel")
    #print test.comboselect("frmInstruments", "cboAdd", "UiAutomation.js")
    #print test.comboselect("frmInstruments", "Choose Target", "Choose Target")
    #print test.getobjectlist("frmInstruments")
    #print test.check("frmInstruments", "chkRecordOnce")
    #print test.wait(1)
    #print test.uncheck("frmInstruments", "chkRepeatRecording")
    #print test.uncheck("frmInstruments", "chkPause")
    #print test.verifyuncheck("frmInstruments", "chkPause")
    #print test.verifycheck("frmInstruments", "chkRepeatRecording")
