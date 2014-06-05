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

import re
import fnmatch
from text import Text
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

    def selectrow(self, window_name, object_name, row_text, partial_match = False):
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

        for cell in object_handle.AXRows:
            if re.match(row_text,
                        cell.AXChildren[0].AXValue):
                if not cell.AXSelected:
                    object_handle.activate()
                    cell.AXSelected=True
                else:
                    # Selected
                    pass
                return 1
        raise LdtpServerException(u"Unable to select row: %s" % row_text)

    def multiselect(self, window_name, object_name, row_text_list, partial_match = False):
        """
        Select multiple row

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_text_list: Row list with matching text to select
        @type row_text: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)

        object_handle.activate()
        selected = False
        try:
            window=self._get_front_most_window()
        except (IndexError, ):
            window=self._get_any_window()
        for row_text in row_text_list:
            selected = False
            for cell in object_handle.AXRows:
                parent_cell = cell
                cell = self._getfirstmatchingchild(cell, "(AXTextField|AXStaticText)")
                if not cell:
                    continue
                if re.match(row_text, cell.AXValue):
                    selected = True
                    if not parent_cell.AXSelected:
                        x, y, width, height = self._getobjectsize(parent_cell)
                        window.clickMouseButtonLeftWithMods((x + width / 2,
                                                             y + height / 2),
                                                            ['<command_l>'])
                        # Following selection doesn't work
                        # parent_cell.AXSelected=True
                        self.wait(0.5)
                    else:
                        # Selected
                        pass
                    break
            if not selected:
                raise LdtpServerException(u"Unable to select row: %s" % row_text)
        if not selected:
            raise LdtpServerException(u"Unable to select any row")
        return 1

    def multiremove(self, window_name, object_name, row_text_list, partial_match = False):
        """
        Remove multiple row

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_text_list: Row list with matching text to select
        @type row_text: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)

        object_handle.activate()
        unselected = False
        try:
            window=self._get_front_most_window()
        except (IndexError, ):
            window=self._get_any_window()
        for row_text in row_text_list:
            selected = False
            for cell in object_handle.AXRows:
                parent_cell = cell
                cell = self._getfirstmatchingchild(cell, "(AXTextField|AXStaticText)")
                if not cell:
                    continue
                if re.match(row_text, cell.AXValue):
                    unselected = True
                    if parent_cell.AXSelected:
                        x, y, width, height = self._getobjectsize(parent_cell)
                        window.clickMouseButtonLeftWithMods((x + width / 2,
                                                             y + height / 2),
                                                            ['<command_l>'])
                        # Following selection doesn't work
                        # parent_cell.AXSelected=False
                        self.wait(0.5)
                    else:
                        # Unselected
                        pass
                    break
            if not unselected:
                raise LdtpServerException(u"Unable to select row: %s" % row_text)
        if not unselected:
            raise LdtpServerException(u"Unable to unselect any row")
        return 1

    def selectrowpartialmatch(self, window_name, object_name, row_text):
        """
        Select row partial match

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

        for cell in object_handle.AXRows:
            if re.search(row_text,
                         cell.AXChildren[0].AXValue):
                if not cell.AXSelected:
                    object_handle.activate()
                    cell.AXSelected=True
                else:
                    # Selected
                    pass
                return 1
        raise LdtpServerException(u"Unable to select row: %s" % row_text)

    def selectrowindex(self, window_name, object_name, row_index):
        """
        Select row index

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_index: Row index to select
        @type row_index: integer

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)

        count=len(object_handle.AXRows)
        if row_index < 0 or row_index > count:
            raise LdtpServerException('Row index out of range: %d' % row_index)
        cell=object_handle.AXRows[row_index]
        if not cell.AXSelected:
            object_handle.activate()
            cell.AXSelected=True
        else:
            # Selected
            pass
        return 1

    def selectlastrow(self, window_name, object_name):
        """
        Select last row

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

        cell=object_handle.AXRows[-1]
        if not cell.AXSelected:
            object_handle.activate()
            cell.AXSelected=True
        else:
            # Selected
            pass
        return 1

    def setcellvalue(self, window_name, object_name, row_index,
                     column=0, data=None):
        """
        Set cell value

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_index: Row index to get
        @type row_index: integer
        @param column: Column index to get, default value 0
        @type column: integer
        @param data: data, default value None
                None, used for toggle button
        @type data: string

        @return: 1 on success.
        @rtype: integer
        """
        raise LdtpServerException("Not implemented")

    def getcellvalue(self, window_name, object_name, row_index, column=0):
        """
        Get cell value

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_index: Row index to get
        @type row_index: integer
        @param column: Column index to get, default value 0
        @type column: integer

        @return: cell value on success.
        @rtype: string
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)

        count=len(object_handle.AXRows)
        if row_index < 0 or row_index > count:
            raise LdtpServerException('Row index out of range: %d' % row_index)
        cell=object_handle.AXRows[row_index]
        count=len(cell.AXChildren)
        if column < 0 or column > count:
            raise LdtpServerException('Column index out of range: %d' % column)
        obj=cell.AXChildren[column]
        if not re.search("AXColumn", obj.AXRole):
            obj=cell.AXChildren[column]
        return obj.AXValue

    def getcellsize(self, window_name, object_name, row_index, column=0):
        """
        Get cell size

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_index: Row index to get
        @type row_index: integer
        @param column: Column index to get, default value 0
        @type column: integer

        @return: cell coordinates on success.
        @rtype: list
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)

        count=len(object_handle.AXRows)
        if row_index < 0 or row_index > count:
            raise LdtpServerException('Row index out of range: %d' % row_index)
        cell=object_handle.AXRows[row_index]
        count=len(cell.AXChildren)
        if column < 0 or column > count:
            raise LdtpServerException('Column index out of range: %d' % column)
        obj=cell.AXChildren[column]
        if not re.search("AXColumn", obj.AXRole):
            obj=cell.AXChildren[column]
        return self._getobjectsize(obj)

    def rightclick(self, window_name, object_name, row_text):
        """
        Right click on table cell

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_text: Row text to right click
        @type row_text: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)

        object_handle.activate()
        self.wait(1)
        for cell in object_handle.AXRows:
            cell = self._getfirstmatchingchild(cell, "(AXTextField|AXStaticText)")
            if not cell:
                continue
            if re.match(row_text, cell.AXValue):
                x, y, width, height = self._getobjectsize(cell)
                # Mouse right click on the object
                cell.clickMouseButtonRight((x + width / 2, y + height / 2))
                return 1
        raise LdtpServerException(u'Unable to right click row: %s' % row_text)

    def checkrow(self, window_name, object_name, row_index, column = 0):
        """
        Check row

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_index: Row index to get
        @type row_index: integer
        @param column: Column index to get, default value 0
        @type column: integer

        @return: cell value on success.
        @rtype: string
        """
        raise LdtpServerException("Not implemented")

    def expandtablecell(self, window_name, object_name, row_index, column = 0):
        """
        Expand or contract table cell

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_index: Row index to get
        @type row_index: integer
        @param column: Column index to get, default value 0
        @type column: integer

        @return: cell value on success.
        @rtype: string
        """
        raise LdtpServerException("Not implemented")

    def uncheckrow(self, window_name, object_name, row_index, column = 0):
        """
        Check row

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_index: Row index to get
        @type row_index: integer
        @param column: Column index to get, default value 0
        @type column: integer

        @return: 1 on success.
        @rtype: integer
        """
        raise LdtpServerException("Not implemented")

    def gettablerowindex(self, window_name, object_name, row_text):
        """
        Get table row index matching given text

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_text: Row text to select
        @type row_text: string

        @return: row index matching the text on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)

        index=0
        for cell in object_handle.AXRows:
            if re.match(row_text,
                        cell.AXChildren[0].AXValue):
                return index
            index += 1
        raise LdtpServerException(u"Unable to find row: %s" % row_text)

    def singleclickrow(self, window_name, object_name, row_text):
        """
        Single click row matching given text

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_text: Row text to select
        @type row_text: string

        @return: row index matching the text on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)

        object_handle.activate()
        self.wait(1)
        for cell in object_handle.AXRows:
            cell = self._getfirstmatchingchild(cell, "(AXTextField|AXStaticText)")
            if not cell:
                continue
            if re.match(row_text, cell.AXValue):
                x, y, width, height = self._getobjectsize(cell)
                # Mouse left click on the object
                cell.clickMouseButtonLeft((x + width / 2, y + height / 2))
                return 1
        raise LdtpServerException('Unable to get row text: %s' % row_text)

    def doubleclickrow(self, window_name, object_name, row_text):
        """
        Double click row matching given text

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_text: Row text to select
        @type row_text: string

        @return: row index matching the text on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)

        object_handle.activate()
        self.wait(1)
        for cell in object_handle.AXRows:
            cell = self._getfirstmatchingchild(cell, "(AXTextField|AXStaticText)")
            if not cell:
                continue
            if re.match(row_text, cell.AXValue):
                x, y, width, height = self._getobjectsize(cell)
                # Mouse double click on the object
                cell.doubleClickMouse((x + width / 2, y + height / 2))
                return 1
        raise LdtpServerException('Unable to get row text: %s' % row_text)

    def doubleclickrowindex(self, window_name, object_name, row_index, col_index=0):
        """
        Double click row matching given text

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string
        @param row_index: Row index to click
        @type row_index: integer
        @param col_index: Column index to click
        @type col_index: integer

        @return: row index matching the text on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)

        count=len(object_handle.AXRows)
        if row_index < 0 or row_index > count:
            raise LdtpServerException('Row index out of range: %d' % row_index)
        cell=object_handle.AXRows[row_index]
        self._grabfocus(cell)
        x, y, width, height = self._getobjectsize(cell)
        # Mouse double click on the object
        cell.doubleClickMouse((x + width / 2, y + height / 2))
        return 1

    def verifytablecell(self, window_name, object_name, row_index,
                        column_index, row_text):
        """
        Verify table cell value with given text

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_index: Row index to get
        @type row_index: integer
        @param column_index: Column index to get, default value 0
        @type column_index: integer
        @param row_text: Row text to match
        @type string

        @return: 1 on success 0 on failure.
        @rtype: integer
        """
        try:
            value=getcellvalue(window_name, object_name, row_index, column_index)
            if re.match(row_text, value):
                return 1
        except LdtpServerException:
            pass
        return 0

    def doesrowexist(self, window_name, object_name, row_text,
                     partial_match = False):
        """
        Verify table cell value with given text

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_text: Row text to match
        @type string
        @param partial_match: Find partial match strings
        @type boolean

        @return: 1 on success 0 on failure.
        @rtype: integer
        """
        try:
            object_handle=self._get_object_handle(window_name, object_name)
            if not object_handle.AXEnabled:
                return 0

            for cell in object_handle.AXRows:
                if not partial_match and re.match(row_text,
                                                  cell.AXChildren[0].AXValue):
                    return 1
                elif partial_match and re.search(row_text,
                                                 cell.AXChildren[0].AXValue):
                    return 1
        except LdtpServerException:
            pass
        return 0

    def verifypartialtablecell(self, window_name, object_name, row_index,
                               column_index, row_text):
        """
        Verify partial table cell value

        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param row_index: Row index to get
        @type row_index: integer
        @param column_index: Column index to get, default value 0
        @type column_index: integer
        @param row_text: Row text to match
        @type string

        @return: 1 on success 0 on failure.
        @rtype: integer
        """
        try:
            value=getcellvalue(window_name, object_name, row_index, column_index)
            if re.searchmatch(row_text, value):
                return 1
        except LdtpServerException:
            pass
        return 0
