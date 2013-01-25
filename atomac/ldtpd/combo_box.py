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
"""Combobox class."""

import re
from atomac import AXKeyCodeConstants

from utils import Utils
from server_exception import LdtpServerException

class ComboBox(Utils):
    def selectitem(self, window_name, object_name, item_name):
        """
        Select combo box / layered pane item
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param item_name: Item name to select
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        self._grabfocus(object_handle.AXWindow)
        try:
            object_handle.Press()
        except AttributeError:
            # AXPress doesn't work with Instruments
            # So did the following work around
            x, y, width, height=self._getobjectsize(object_handle)
            # Mouse left click on the object
            # Note: x + width/2, y + height / 2 doesn't work
            self.generatemouseevent(x + 5, y + 5, "b1c")
            self.wait(5)
            handle=self._get_sub_menu_handle(object_handle, item_name)
            x, y, width, height=self._getobjectsize(handle)
            # on OSX 10.7 default "b1c" doesn't work
            # so using "b1d", verified with Fusion test, this works
            self.generatemouseevent(x + 5, y + 5, "b1d")
            return 1
        # Required for menuitem to appear in accessibility list
        self.wait(1)
        menu_list=re.split(";", item_name)
        try:
            menu_handle=self._internal_menu_handler(object_handle, menu_list,
                                                    True)
            # Required for menuitem to appear in accessibility list
            self.wait(1)
            if not menu_handle.AXEnabled:
                raise LdtpServerException(u"Object %s state disabled" % \
                                          menu_list[-1])
            menu_handle.Press()
        except LdtpServerException:
            object_handle.activate()
            object_handle.sendKey(AXKeyCodeConstants.ESCAPE)
            raise
        return 1

    # Since selectitem and comboselect implementation are same,
    # for Linux/Windows API compatibility let us assign selectitem to comboselect
    comboselect=selectitem

    def selectindex(self, window_name, object_name, item_index):
        """
        Select combo box item / layered pane based on index
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param item_index: Item index to select
        @type object_name: integer

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        self._grabfocus(object_handle.AXWindow)
        try:
            object_handle.Press()
        except AttributeError:
            # AXPress doesn't work with Instruments
            # So did the following work around
            x, y, width, height=self._getobjectsize(object_handle)
            # Mouse left click on the object
            # Note: x + width/2, y + height / 2 doesn't work
            self.generatemouseevent(x + 5, y + 5, "b1c")
        # Required for menuitem to appear in accessibility list
        self.wait(2)
        if not object_handle.AXChildren:
            raise LdtpServerException(u"Unable to find menu")
        # Get AXMenu
        children=object_handle.AXChildren[0]
        if not children:
            raise LdtpServerException(u"Unable to find menu")
        children=children.AXChildren
        tmp_children=[]
        for child in children:
            role, label=self._ldtpize_accessible(child)
            # Don't add empty label
            # Menu separator have empty label's
            if label:
                tmp_children.append(child)
        children=tmp_children
        length=len(children)
        try:
            if item_index < 0 or item_index > length:
                raise LdtpServerException(u"Invalid item index %d" % item_index)
            menu_handle=children[item_index]
            if not menu_handle.AXEnabled:
                raise LdtpServerException(u"Object %s state disabled" % menu_list[-1])
            self._grabfocus(menu_handle)
            x, y, width, height=self._getobjectsize(menu_handle)
            # on OSX 10.7 default "b1c" doesn't work
            # so using "b1d", verified with Fusion test, this works
            window=object_handle.AXWindow
            # For some reason,
            # self.generatemouseevent(x + 5, y + 5, "b1d")
            # doesn't work with Fusion settings
            # Advanced window, so work around with this
            # ldtp.selectindex('*Advanced', 'Automatic', 1)
            """
            Traceback (most recent call last):
               File "build/bdist.macosx-10.8-intel/egg/atomac/ldtpd/utils.py", line 178, in _dispatch
                  return getattr(self, method)(*args)
               File "build/bdist.macosx-10.8-intel/egg/atomac/ldtpd/combo_box.py", line 146, in selectindex
                  self.generatemouseevent(x + 5, y + 5, "b1d")
               File "build/bdist.macosx-10.8-intel/egg/atomac/ldtpd/mouse.py", line 97, in generatemouseevent
                  window=self._get_front_most_window()
               File "build/bdist.macosx-10.8-intel/egg/atomac/ldtpd/utils.py", line 185, in _get_front_most_window
                  front_app=atomac.NativeUIElement.getFrontmostApp()
               File "build/bdist.macosx-10.8-intel/egg/atomac/AXClasses.py", line 114, in getFrontmostApp
                  raise ValueError('No GUI application found.')
            ValueError: No GUI application found.
            """
            window.doubleClickMouse((x + 5, y + 5))
            # If menuitem already pressed, set child to None
            # So, it doesn't click back in combobox in finally block
            child=None
        finally:
            if child:
                child.Cancel()
        return 1

    # Since selectindex and comboselectindex implementation are same,
    # for backward compatibility let us assign selectindex to comboselectindex
    comboselectindex=selectindex

    def getallitem(self, window_name, object_name):
        """
        Get all combo box item

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: list of string on success.
        @rtype: list
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        object_handle.Press()
        # Required for menuitem to appear in accessibility list
        self.wait(1)
        child=None
        try:
            if not object_handle.AXChildren:
                raise LdtpServerException(u"Unable to find menu")
            # Get AXMenu
            children=object_handle.AXChildren[0]
            if not children:
                raise LdtpServerException(u"Unable to find menu")
            children=children.AXChildren
            items=[]
            for child in children:
                label = self._get_title(child)
                # Don't add empty label
                # Menu separator have empty label's
                if label:
                    items.append(label)
        finally:
            if child:
                # Set it back, by clicking combo box
                child.Cancel()
        return items

    def showlist(self, window_name, object_name):
        """
        Show combo box list / menu
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
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

    def hidelist(self, window_name, object_name):
        """
        Hide combo box list / menu
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        object_handle.activate()
        object_handle.sendKey(AXKeyCodeConstants.ESCAPE)
        return 1

    def verifydropdown(self, window_name, object_name):
        """
        Verify drop down list / menu poped up
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success 0 on failure.
        @rtype: integer
        """
        try:
            object_handle=self._get_object_handle(window_name, object_name)
            if not object_handle.AXEnabled or not object_handle.AXChildren:
                return 0
            # Get AXMenu
            children=object_handle.AXChildren[0]
            if children:
                return 1
        except LdtpServerException:
            pass
        return 0

    def verifyshowlist(self, window_name, object_name):
        """
        Verify drop down list / menu poped up
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success 0 on failure.
        @rtype: integer
        """
        return self.verifydropdown(window_name, object_name)

    def verifyhidelist(self, window_name, object_name):
        """
        Verify list / menu is hidden in combo box
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success 0 on failure.
        @rtype: integer
        """
        try:
            object_handle=self._get_object_handle(window_name, object_name)
            if not object_handle.AXEnabled:
                return 0
            if not object_handle.AXChildren:
                return 1
            # Get AXMenu
            children=object_handle.AXChildren[0]
            if not children:
                return 1
            return 1
        except LdtpServerException:
            pass
        return 0

    def verifyselect(self, window_name, object_name, item_name):
        """
        Verify the item selected in combo box
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param item_name: Item name to select
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        try:
            object_handle=self._get_object_handle(window_name, object_name)
            if not object_handle.AXEnabled:
                return 0
            role, label=self._ldtpize_accessible(object_handle)
            title=self._get_title(object_handle)
            if re.match(item_name, title, re.M | re.U | re.L) or \
                    re.match(item_name, label, re.M | re.U | re.L) or \
                    re.match(item_name, u"%u%u" % (role, label),
                             re.M | re.U | re.L):
                return 1
        except LdtpServerException:
            pass
        return 0

    def getcombovalue(self, window_name, object_name):
        """
        Get current selected combobox value
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: selected item on success, else LdtpExecutionError on failure.
        @rtype: string
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        return self._get_title(object_handle)
