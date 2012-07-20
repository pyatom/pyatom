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
from utils import Utils
from combo_box import ComboBox
from page_tab_list import PageTabList
from server_exception import LdtpServerException

class Core(ComboBox, Menu, Mouse, PageTabList, Text, Table, Value):
    def __init__(self):
        super(Core, self).__init__()

    """Core LDTP class"""
    def getapplist(self):
        """
        Get all accessibility application name that are currently running
        
        @return: list of appliction name of string type on success.
        @rtype: list
        """
        app_list=[]
        for gui in self._running_apps:
            app_list.append(gui.localizedName())
        # Return unique application list
        return list(set(app_list))

    def getwindowlist(self):
        """
        Get all accessibility window that are currently open
        
        @return: list of window names in LDTP format of string type on success.
        @rtype: list
        """
        return self._get_windows().keys()

    def isalive(self):
        """
        Client will use this to verify whether the server instance is alive or not.

        @return: True on success.
        @rtype: boolean
        """

        return True

    def getobjectlist(self, window_name):
        """
        Get list of items in given GUI.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: list of items in LDTP naming convention.
        @rtype: list
        """
        if not window_name:
            raise LdtpServerException(u"Invalid argument window_name")
        window_handle, name, app=self._get_window_handle(window_name)
        object_list=self._get_appmap(window_handle, name)
        return object_list.keys()

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
        object_handle.Press()
        return 1

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
        self.grabfocus(object_handle)
        x, y, width, height=self.getobjectsize(object_handle)
        # Mouse left click on the object
        # Note: x + width/2, y + height / 2 doesn't work
        object_handle.clickMouseButtonLeft((x + width / 2, y + height / 2))
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
        self.grabfocus(object_handle)
        x, y, width, height=self.getobjectsize(object_handle)
        # Mouse left click on the object
        # Note: x + width/2, y + height / 2 doesn't work
        object_handle.clickMouseButtonLeft((x + width / 2, y + height / 2))
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

if __name__ == "__main__":
    test=Core()
    #apps=test.getapplist()
    #windows=test.getwindowlist()
    #print test.guiexist("gedit")
    #print test.guiexist("gedit", "txt0")
    #print test.guiexist("Open")
    #print test.guiexist("Open", "btnCancel")
    #print test.guiexist("Open", "C0ncel")
    #print "waittillguiexist"
    #print test.waittillguiexist("Open")
    #print test.waittillguiexist("Open", "btnCancel")
    #print test.waittillguiexist("Open", "C0ncel", 10)
    #print "waittillguinotexist"
    #print test.waittillguinotexist("Open", guiTimeOut=5)
    #print test.waittillguinotexist("Open", "btnCancel", 5)
    #print test.waittillguinotexist("Open", "C0ncel")
    #print windows
    #objList = test.getobjectlist("frmTryitEditorv1.5")
    #for obj in objList:
        #if re.search("^tbl\d", obj):
            #print obj, test.getrowcount("frmTryitEditorv1.5", obj)
    #print test.selectrow("Accounts", "tbl0", "VMware")
    #print test.scrollup("Downloads", "scbr0")
    #print test.oneright("Downloads", "scbr1", 3)
    #print len(apps), len(windows)
    #print apps, windows
    #print test.getobjectlist("Contacts")
    #print test.click("Open", "Cancel")
    #print test.comboselect("frmInstruments", "cboAdd", "UiAutomation.js")
    #print test.comboselect("frmInstruments", "Choose Target", "Choose Target;Octopus")
    #print test.getobjectlist("frmInstruments")
    #print test.check("frmInstruments", "chkRecordOnce")
    #print test.wait(1)
    #print test.uncheck("frmInstruments", "chkRepeatRecording")
    #print test.uncheck("frmInstruments", "chkPause")
    #print test.verifyuncheck("frmInstruments", "chkPause")
    #print test.verifycheck("frmInstruments", "chkRepeatRecording")
    #print test.doesmenuitemexist("Instru*", "File;Open...")
    #print test.doesmenuitemexist("Instruments*", "File;Open...")
    #print test.doesmenuitemexist("Instruments*", "File;Open*")
    #print test.selectmenuitem("Instruments*", "File;Open*")
    #print test.checkmenu("Instruments*", "View;Instruments")
    #test.wait(1)
    #print test.checkmenu("Instruments*", "View;Instruments")
    #print test.uncheckmenu("Instruments*", "View;Instruments")
    #test.wait(1)
    #print test.verifymenucheck("Instruments*", "View;Instruments")
    #print test.verifymenuuncheck("Instruments*", "View;Instruments")
    #print test.checkmenu("Instruments*", "View;Instruments")
    #test.wait(1)
    #print test.verifymenucheck("Instruments*", "View;Instruments")
    #print test.verifymenuuncheck("Instruments*", "View;Instruments")
    #print test.mouseleftclick("Open", "Cancel")
    #a=test.getobjectlist("Open")
    #for i in a:
    #    if i.find("txt") != -1:
    #        print i
    #print test.settextvalue("Open", "txttextfield", "pyatom ldtp")
    #print test.gettextvalue("Open", "txttextfield")
    #print test.getcharcount("Open", "txttextfield")
    #print test.menuitemenabled("Instruments*", "File;Record Trace")
    #print test.menuitemenabled("Instruments*", "File;Pause Trace")
    #print test.listsubmenus("Instruments*", "Fi*")
    #print test.listsubmenus("Instruments*", "File;OpenRecent")
    #print test.listsubmenus("Instruments*", "File;mnuOpenRecent")
    #print test.listsubmenus("Instruments*", "File;GetInfo")
    #try:
    #    print test.listsubmenus("Instruments*", "File;ding")
    #except LdtpServerException:
    #    pass
    #try:
    #    print test.listsubmenus("Instruments*", "ding")
    #except LdtpServerException:
    #    pass
    #try:
    #    print test.listsubmenus("ding", "dong")
    #except LdtpServerException:
    #    pass
    #print test.getcursorposition("Open", "txttextfield")
    #print test.setcursorposition("Open", "txttextfield", 10)
    #print test.cuttext("Open", "txttextfield", 2)
    #print test.cuttext("Open", "txttextfield", 2, 20)
    #print test.pastetext("Open", "txttextfield", 2)
    #print test.gettabname("*ldtpd*python*", "ptl0", 2)
    #print test.gettabcount("*ldtpd*python*", "ptl0")
    #print test.selecttabindex("*ldtpd*python*", "ptl0", 2)
    #print test.selecttab("*ldtpd*python*", "ptl0", "*bash*")
    #print test.verifytabname("*ldtpd*python*", "ptl0", "*gabe*")
    #print test.selectindex("frmInstruments", "cboAdd", 1)
    #print test.getallitem("frmInstruments", "cboAdd")
    #print test.selectindex("frmInstruments", "cboAdd", 10)
    #print test.showlist("frmInstruments", "cboAdd")
    #test.wait(1)
    #print test.verifydropdown("frmInstruments", "cboAdd")
    #print test.hidelist("frmInstruments", "cboAdd")
    #test.wait(1)
    #print test.verifydropdown("frmInstruments", "cboAdd")
    #print test.showlist("frmInstruments", "cboAdd")
    #test.wait(1)
    #print test.verifyshowlist("frmInstruments", "cboAdd")
    #print test.hidelist("frmInstruments", "cboAdd")
    #test.wait(1)
    #print test.verifyhidelist("frmInstruments", "cboAdd")
    #print test.comboselect("frmInstruments", "lst0", "Trace Log")
