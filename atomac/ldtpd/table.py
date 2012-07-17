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
"""Mouse class."""

from utils import Utils
from server_exception import LdtpServerException

class Table(Utils):
    def getrowcount(self, window_name, object_name):
        """
        Get count of rows in table object.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: Number of rows.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        return len(object_handle.AXRows)

    def selectrow(self, window_name, object_name, row_text):
        """
        Select row
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_text: Row text to select
        @type row_text: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        print len(object_handle.AXRows)
        print dir(object_handle), type(object_handle), object_handle.AXVisibleCells

        for cell in object_handle.AXVisibleCells:
            print cell, cell.AXSelected, dir(cell.AXSelected)
        print dir(cell)
        raise LdtpServerException('Unable to select row: %s' % row_text)
