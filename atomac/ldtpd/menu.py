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
"""Menu class."""

import re
import atomac

from utils import Utils
from server_exception import LdtpServerException

class Menu(Utils):
    def _internal_menu_handler(self, window_name, object_name,
                               wait_for_window = True):
        window_handle, name, app = self._get_window_handle(window_name,
                                                           wait_for_window)
        if not window_handle:
            raise LdtpServerException(u"Unable to find window %s" % window_name)
        menu_list = object_name.split(";")
        # pyatom doesn't understand LDTP convention mnu, strip it off
        menu_handle = app.menuItem(re.sub("mnu", "", menu_list[0]))
        if not menu_handle:
            raise LdtpServerException(u"Unable to find menu %s" % menu_list[0])
        if len(menu_list) <= 1:
            # If only first level menu is given, return the handle
            return menu_handle
        menu_handle_found = False
        for menu in menu_list[1:]:
            menu_handle_found = False
            children = menu_handle.AXChildren[0]
            if not children:
                raise LdtpServerException(u"Unable to find menu %s" % menu)
            tmp_menu = fnmatch.translate(menu)
            for current_menu in children.AXChildren:
                role, label = self._ldtpize_accessible(current_menu)
                if re.match(tmp_menu, label) or \
                    re.match(tmp_menu, u"%s%s" % (role, label)):
                    menu_handle = current_menu
                    menu_handle_found = True
                    break
            if not menu_handle_found:
                raise LdtpServerException(u"Unable to find menu %s" % menu)
        return menu_handle

    def selectmenuitem(self, window_name, object_name):
        """
        Select (click) a menu item.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        menu_handle = self._internal_menu_handler(window_name, object_name)
        if not menu_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        menu_handle.Press()
        return 1

    def doesmenuitemexist(self, window_name, object_name):
        """
        Check a menu item exist.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string
        @param strict_hierarchy: Mandate menu hierarchy if set to True
        @type object_name: boolean

        @return: 1 on success.
        @rtype: integer
        """
        try:
            menu_handle = self._internal_menu_handler(window_name, object_name,
                                                      False)
            return 1
        except LdtpServerException:
            return 0

    def menuitemenabled(self, window_name, object_name):
        """
        Verify a menu item is enabled

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        try:
            menu_handle = self._internal_menu_handler(window_name, object_name,
                                                      False)
            if menu_handle.AXEnabled:
                return 1
        except LdtpServerException:
            pass
        return 0

    def listsubmenus(self, window_name, object_name):
        """
        List children of menu item
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: menu item in list on success.
        @rtype: list
        """
        menu_handle = self._internal_menu_handler(window_name, object_name)
        role, label = self._ldtpize_accessible(menu_handle) 
        if not menu_handle.AXChildren:
            raise LdtpServerException(u"Unable to find children under menu %s" % \
                                      label)
        children = menu_handle.AXChildren[0]
        sub_menus = []
        for current_menu in children.AXChildren:
            role, label = self._ldtpize_accessible(current_menu)
            if not label:
                # All splitters have empty label
                continue
            sub_menus.append(u"%s%s" % (role, label))
        return sub_menus

    def verifymenucheck(self, window_name, object_name):
        """
        Verify a menu item is checked

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        try:
            menu_handle = self._internal_menu_handler(window_name, object_name,
                                                      False)
            try:
                if menu_handle.AXMenuItemMarkChar:
                    # Checked
                    return 1
            except atomac._a11y.Error:
                pass
        except LdtpServerException:
            pass
        return 0

    def verifymenuuncheck(self, window_name, object_name):
        """
        Verify a menu item is un-checked

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        try:
            menu_handle = self._internal_menu_handler(window_name, object_name,
                                                      False)
            try:
                if not menu_handle.AXMenuItemMarkChar:
                    # Unchecked
                    return 1
            except atomac._a11y.Error:
                return 1
        except LdtpServerException:
            pass
        return 0

    def menucheck(self, window_name, object_name):
        """
        Check (click) a menu item.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        menu_handle = self._internal_menu_handler(window_name, object_name)
        if not menu_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        try:
            if menu_handle.AXMenuItemMarkChar:
                # Already checked
                return 1
        except atomac._a11y.Error:
            pass
        menu_handle.Press()
        return 1

    def menuuncheck(self, window_name, object_name):
        """
        Uncheck (click) a menu item.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        menu_handle = self._internal_menu_handler(window_name, object_name)
        if not menu_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        try:
            if not menu_handle.AXMenuItemMarkChar:
                # Already unchecked
                return 1
        except atomac._a11y.Error:
            return 1
        menu_handle.Press()
        return 1
