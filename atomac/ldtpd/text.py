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
"""Text class."""

import re

from utils import Utils
from server_exception import LdtpServerException

class Text(Utils):
    def generatekeyevent(self, data):
        """
        Functionality of generatekeyevent is similar to typekey of 
        LTFX project.
        
        @param data: data to type.
        @type data: string

        @return: 1 on success.
        @rtype: integer
        """
        raise LdtpServerException("Not implemented")

    def keypress(self, data):
        """
        Press key. NOTE: keyrelease should be called

        @param data: data to type.
        @type data: string

        @return: 1 on success.
        @rtype: integer
        """
        raise LdtpServerException("Not implemented")

    def keyrelease(self, data):
        """
        Release key. NOTE: keypress should be called before this

        @param data: data to type.
        @type data: string

        @return: 1 on success.
        @rtype: integer
        """
        raise LdtpServerException("Not implemented")

    def enterstring(self, window_name, object_name='', data=''):
        """
        Type string sequence.
        
        @param window_name: Window name to focus on, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to focus on, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param data: data to type.
        @type data: string

        @return: 1 on success.
        @rtype: integer
        """
        raise LdtpServerException("Not implemented")

    def settextvalue(self, window_name, object_name, data):
        """
        Type string sequence.
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param data: data to type.
        @type data: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle = self._get_object_handle(window_name, object_name)
        if not object_handle:
            raise LdtpServerException(u"Unable to find object %s" % object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        object_handle.AXValue = data
        return 1

    def gettextvalue(self, window_name, object_name):
        """
        Get text value
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param startPosition: Starting position of text to fetch
        @type: startPosition: int
        @param endPosition: Ending position of text to fetch
        @type: endPosition: int

        @return: text on success.
        @rtype: string
        """
        object_handle = self._get_object_handle(window_name, object_name)
        if not object_handle:
            raise LdtpServerException(u"Unable to find object %s" % object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        return object_handle.AXValue

    def verifypartialmatch(self, window_name, object_name, partial_text):
        """
        Verify partial text
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param partial_text: Partial text to match
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        try:
            if re.search(partial_text,
                         self.gettextvalue(window_name,
                                           object_name)):
                return 1
        except:
            pass
        return 0

    def verifysettext(self, window_name, object_name, text):
        """
        Verify text is set correctly
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param text: text to match
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        try:
            return int(self._glob_match(text,
                                        self.gettextvalue(window_name,
                                                          object_name)))
        except:
            return 0

    def istextstateenabled(self, window_name, object_name):
        """
        Verifies text state enabled or not
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success 0 on failure.
        @rtype: integer
        """
        object_handle = self._get_object_handle(window_name, object_name)
        if not object_handle:
            return 0
        if not object_handle.AXEnabled:
            return 0
        return 1

    def getcharcount(self, window_name, object_name):
        """
        Get character count
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle = self._get_object_handle(window_name, object_name)
        if not object_handle:
            raise LdtpServerException(u"Unable to find object %s" % object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        return object_handle.AXNumberOfCharacters

    def appendtext(self, window_name, object_name, data):
        """
        Append string sequence.
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param data: data to type.
        @type data: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle = self._get_object_handle(window_name, object_name)
        if not object_handle:
            raise LdtpServerException(u"Unable to find object %s" % object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        object_handle.AXValue += data
        return 1

    def getcursorposition(self, window_name, object_name):
        """
        Get cursor position
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: Cursor position on success.
        @rtype: integer
        """
        object_handle = self._get_object_handle(window_name, object_name)
        if not object_handle:
            raise LdtpServerException(u"Unable to find object %s" % object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        print object_handle
        #print object_handle.AXSelectedTextRange
        print object_handle.AXSelectedTextRange.loc
        return -1
