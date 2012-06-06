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
"""Combobox class."""

import re

from utils import Utils
from server_exception import LdtpServerException

class Menu(Utils):
    def selectmenuitem(self, window_name, object_name):
        window_handle, name, app = self._get_window_handle(window_name)
        if not window_handle:
            raise LdtpServerException(u"Unable to find window %s" % window_name)
        menu_list = object_name.split(";")
        menu_handle = app.menuItem(*menu_list)
        if not menu_handle:
            raise LdtpServerException(u"Unable to find menu %s" % object_name)
        if not menu_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        menu_handle.Press()
        return 1

    def doesmenuitemexist(self, window_name, object_name):
        window_handle, name, app = self._get_window_handle(window_name, False)
        if not window_handle:
            return 0
        menu_list = object_name.split(";")
        menu_handle = app.menuItem(*menu_list)
        if not menu_handle:
            return 0
        return 1

    def menuitemenabled(self, window_name, object_name):
        window_handle, name, app = self._get_window_handle(window_name, False)
        if not window_handle:
            return 0
        menu_list = object_name.split(";")
        menu_handle = app.menuItem(*menu_list)
        if not menu_handle:
            return 0
        if not menu_handle.AXEnabled:
            return 0
        return 1

    def verifymenucheck(self, window_name, object_name):
        window_handle, name, app = self._get_window_handle(window_name, False)
        if not window_handle:
            return 0
        menu_list = object_name.split(";")
        menu_handle = app.menuItem(*menu_list)
        if not menu_handle:
            return 0
        try:
            if menu_handle.AXMenuItemMarkChar:
                # Already checked
                return 1
        except atomac._a11y.Error:
            pass
        return 0

    def verifymenuuncheck(self, window_name, object_name):
        window_handle, name, app = self._get_window_handle(window_name, False)
        if not window_handle:
            return 0
        menu_list = object_name.split(";")
        menu_handle = app.menuItem(*menu_list)
        if not menu_handle:
            return 0
        try:
            if not menu_handle.AXMenuItemMarkChar:
                # Already unchecked
                return 1
        except atomac._a11y.Error:
            return 1
        return 0

    def checkmenu(self, window_name, object_name):
        window_handle, name, app = self._get_window_handle(window_name)
        if not window_handle:
            raise LdtpServerException(u"Unable to find window %s" % window_name)
        menu_list = object_name.split(";")
        menu_handle = app.menuItem(*menu_list)
        if not menu_handle:
            raise LdtpServerException(u"Unable to find menu %s" % object_name)
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

    def uncheckmenu(self, window_name, object_name):
        window_handle, name, app = self._get_window_handle(window_name)
        if not window_handle:
            raise LdtpServerException(u"Unable to find window %s" % window_name)
        menu_list = object_name.split(";")
        menu_handle = app.menuItem(*menu_list)
        if not menu_handle:
            raise LdtpServerException(u"Unable to find menu %s" % object_name)
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
