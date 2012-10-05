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
"""Text class."""

import re
import fnmatch
import atomac.Clipboard as Clipboard

from utils import Utils
from keypress_actions import KeyComboAction, KeyPressAction, KeyReleaseAction
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
        window=self._get_front_most_window()
        key_combo_action = KeyComboAction(window, data)

    def keypress(self, data):
        """
        Press key. NOTE: keyrelease should be called

        @param data: data to type.
        @type data: string

        @return: 1 on success.
        @rtype: integer
        """
        window=self._get_front_most_window()
        key_press_action = KeyPressAction(window, data)

    def keyrelease(self, data):
        """
        Release key. NOTE: keypress should be called before this

        @param data: data to type.
        @type data: string

        @return: 1 on success.
        @rtype: integer
        """
        window=self._get_front_most_window()
        key_release_action = KeyReleaseAction(window, data)

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
        if not object_name and not data:
            raise LdtpServerException("Not implemented")
        else:
            object_handle=self._get_object_handle(window_name, object_name)
            if not object_handle.AXEnabled:
                raise LdtpServerException(u"Object %s state disabled" % object_name)
            object_handle.sendKey(data)

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
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        object_handle.AXValue=data
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
        object_handle=self._get_object_handle(window_name, object_name)
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
            if re.search(fnmatch.translate(partial_text),
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
            return int(re.match(fnmatch.translate(text),
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
        try:
            object_handle=self._get_object_handle(window_name, object_name)
            if object_handle.AXEnabled:
                return 1
        except LdtpServerException:
            pass
        return 0

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
        object_handle=self._get_object_handle(window_name, object_name)
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
        object_handle=self._get_object_handle(window_name, object_name)
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
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        return object_handle.AXSelectedTextRange.loc

    def setcursorposition(self, window_name, object_name, cursor_position):
        """
        Set cursor position
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param cursor_position: Cursor position to be set
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        object_handle.AXSelectedTextRange.loc=cursor_position
        return 1

    def cuttext(self, window_name, object_name, start_position, end_position=-1):
        """
        cut text from start position to end position
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param start_position: Start position
        @type object_name: integer
        @param end_position: End position, default -1
        Cut all the text from start position till end
        @type object_name: integer

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        size=object_handle.AXNumberOfCharacters
        if end_position == -1 or end_position > size:
            end_position=size
        if start_position < 0:
            start_position=0
        data=object_handle.AXValue
        Clipboard.copy(data[start_position:end_position])
        object_handle.AXValue=data[:start_position] + data[end_position:]
        return 1

    def copytext(self, window_name, object_name, start_position, end_position=-1):
        """
        copy text from start position to end position
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param start_position: Start position
        @type object_name: integer
        @param end_position: End position, default -1
        Copy all the text from start position till end
        @type object_name: integer

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        size=object_handle.AXNumberOfCharacters
        if end_position == -1 or end_position > size:
            end_position=size
        if start_position < 0:
            start_position=0
        data=object_handle.AXValue
        Clipboard.copy(data[start_position:end_position])
        return 1


    def deletetext(self, window_name, object_name, start_position, end_position=-1):
        """
        delete text from start position to end position
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param start_position: Start position
        @type object_name: integer
        @param end_position: End position, default -1
        Delete all the text from start position till end
        @type object_name: integer

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        size=object_handle.AXNumberOfCharacters
        if end_position == -1 or end_position > size:
            end_position=size
        if start_position < 0:
            start_position=0
        data=object_handle.AXValue
        object_handle.AXValue=data[:start_position] + data[end_position:]
        return 1

    def pastetext(self, window_name, object_name, position=0):
        """
        paste text from start position to end position
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param position: Position to paste the text, default 0
        @type object_name: integer

        @return: 1 on success.
        @rtype: integer
        """
        object_handle=self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        size=object_handle.AXNumberOfCharacters
        if position > size:
            position=size
        if position < 0:
            position=0
        clipboard=Clipboard.paste()
        data=object_handle.AXValue
        object_handle.AXValue=data[:position] + clipboard + data[position:]
        return 1
