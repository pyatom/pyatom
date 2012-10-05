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
"""PageTabList class."""

import re
import fnmatch

from utils import Utils
from server_exception import LdtpServerException

class PageTabList(Utils):
    def _get_tab_children(self, window_name, object_name):
        object_handle = self._get_object_handle(window_name, object_name)
        if not object_handle:
            raise LdtpServerException(u"Unable to find object %s" % object_name)
        return object_handle.AXChildren

    def _get_tab_handle(self, window_name, object_name, tab_name):
        children = self._get_tab_children(window_name, object_name)
        tab_handle = None
        for current_tab in children:
            role, label = self._ldtpize_accessible(current_tab)
            tmp_tab_name = fnmatch.translate(tab_name)
            if re.match(tmp_tab_name, label) or \
                    re.match(tmp_tab_name, u"%s%s" % (role, label)):
                tab_handle = current_tab
                break
        if not tab_handle:
            raise LdtpServerException(u"Unable to find tab %s" % tab_name)
        if not tab_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        return tab_handle

    def selecttab(self, window_name, object_name, tab_name):
        """
        Select tab based on name.
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param tab_name: tab to select
        @type data: string

        @return: 1 on success.
        @rtype: integer
        """
        tab_handle = self._get_tab_handle(window_name, object_name, tab_name)
        tab_handle.Press()
        return 1

    def selecttabindex(self, window_name, object_name, tab_index):
        """
        Select tab based on index.
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param tab_index: tab to select
        @type data: integer

        @return: 1 on success.
        @rtype: integer
        """
        children = self._get_tab_children(window_name, object_name)
        length = len(children)
        if tab_index < 0 or tab_index > length:
            raise LdtpServerException(u"Invalid tab index %s" % tab_index)
        tab_handle = children[tab_index]
        if not tab_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        tab_handle.Press()
        return 1

    def verifytabname(self, window_name, object_name, tab_name):
        """
        Verify tab name.
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param tab_name: tab to select
        @type data: string

        @return: 1 on success 0 on failure
        @rtype: integer
        """
        try:
            tab_handle = self._get_tab_handle(window_name, object_name, tab_name)
            if tab_handle.AXValue:
                return 1
        except LdtpServerException:
            pass
        return 0

    def gettabcount(self, window_name, object_name):
        """
        Get tab count.
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: tab count on success.
        @rtype: integer
        """
        children = self._get_tab_children(window_name, object_name)
        return len(children)

    def gettabname(self, window_name, object_name, tab_index):
        """
        Get tab name
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param tab_index: Index of tab (zero based index)
        @type object_name: int

        @return: text on success.
        @rtype: string
        """
        children = self._get_tab_children(window_name, object_name)
        length = len(children)
        if tab_index < 0 or tab_index > length:
            raise LdtpServerException(u"Invalid tab index %s" % tab_index)
        tab_handle = children[tab_index]
        if not tab_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        return tab_handle.AXTitle
