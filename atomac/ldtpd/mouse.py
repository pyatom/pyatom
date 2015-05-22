 # -*- coding: utf-8 -*-

# Copyright (c) 2012 VMware, Inc. All Rights Reserved.

# This file is part of ATOMac.

#@author: Nagappan Alagappan <nagappan@gmail.com>
#@copyright: Copyright (c) 2009-14 Nagappan Alagappan
#@author: Sigbjørn Vik <sigbjorn@opera.com>
#@Copyright (C) 2013-14 Opera Software ASA (generatemouseevent API).
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

import time
from Quartz import CGEventCreateMouseEvent,\
                  CGEventPost,\
                  kCGHIDEventTap,\
                  CGEventSetIntegerValueField,\
                  kCGMouseEventClickState,\
                  CGEventGetLocation,\
                  CGEventCreate
from Quartz import kCGEventMouseMoved as move
from Quartz import kCGEventLeftMouseDown as press_left
from Quartz import kCGEventLeftMouseUp as release_left
from Quartz import kCGEventLeftMouseDragged as drag_left
from Quartz import kCGEventRightMouseDown as press_right
from Quartz import kCGEventRightMouseUp as release_right
from Quartz import kCGEventRightMouseDragged as drag_right
from Quartz import kCGEventOtherMouseDown as press_other
from Quartz import kCGEventOtherMouseUp as release_other
from Quartz import kCGEventOtherMouseDragged as drag_other

from Quartz import kCGMouseButtonLeft as left
from Quartz import kCGMouseButtonRight as right
from Quartz import kCGMouseButtonCenter as centre

from utils import Utils
from server_exception import LdtpServerException

single_click = 1
double_click = 2
triple_click = 3

drag_default_button = 100

# Global value to remember if any button should be down during moves
drag_button_remembered = None

mouse_click_override = {'single_click': single_click, 'double_click': double_click,
                        'triple_click': triple_click, 'move': move,
                        'press_left': press_left, 'release_left': release_left,
                        'drag_left': drag_left, 'press_right': press_right,
                        'release_right': release_right, 'drag_right': drag_right,
                        'press_other': press_other, 'release_other': release_other,
                        'drag_other': drag_other, 'left': left, 'right': right,
                        'centre': centre, 'drag_default_button': drag_default_button}

class Mouse(Utils):
    def mouseleftclick(self, window_name, object_name):
        """
        Mouse left click on an object.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle = self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        self._grabfocus(object_handle)
        x, y, width, height = self._getobjectsize(object_handle)
        # Mouse left click on the object
        object_handle.clickMouseButtonLeft((x + width / 2, y + height / 2))
        return 1

    def mouserightclick(self, window_name, object_name):
        """
        Mouse right click on an object.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle = self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        self._grabfocus(object_handle)
        x, y, width, height = self._getobjectsize(object_handle)
        # Mouse right click on the object
        object_handle.clickMouseButtonRight((x + width / 2, y + height / 2))
        return 1

    def generatemouseevent(self, x, y, eventType="b1c",
                           drag_button_override='drag_default_button'):
        """
        Generate mouse event on x, y co-ordinates.
        
        @param x: X co-ordinate
        @type x: int
        @param y: Y co-ordinate
        @type y: int
        @param eventType: Mouse click type
        @type eventType: str
        @param drag_button_override: Any drag_xxx value
                Only relevant for movements, i.e. |type| = "abs" or "rel"
                Quartz is not fully compatible with windows, so for drags
                the drag button must be explicitly defined. generatemouseevent
                will remember the last button pressed by default, and drag
                that button, use this argument to override that.
        @type drag_button_override: str

        @return: 1 on success.
        @rtype: integer
        """
        if drag_button_override not in mouse_click_override:
            raise ValueError('Unsupported drag_button_override type: %s' % \
                             drag_button_override)
        global drag_button_remembered
        point = (x, y)
        button = centre  # Only matters for "other" buttons
        click_type = None
        if eventType == "abs" or eventType == "rel":
            if drag_button_override is not 'drag_default_button':
                events = [mouse_click_override[drag_button_override]]
            elif drag_button_remembered:
                events = [drag_button_remembered]
            else:
                events = [move]
            if eventType == "rel":
                point = CGEventGetLocation(CGEventCreate(None))
                point.x += x
                point.y += y
        elif eventType == "b1p":
            events = [press_left]
            drag_button_remembered = drag_left
        elif eventType == "b1r":
            events = [release_left]
            drag_button_remembered = None
        elif eventType == "b1c":
            events = [press_left, release_left]
        elif eventType == "b1d":
            events = [press_left, release_left]
            click_type = double_click
        elif eventType == "b2p":
            events = [press_other]
            drag_button_remembered = drag_other
        elif eventType == "b2r":
            events = [release_other]
            drag_button_remembered = None
        elif eventType == "b2c":
            events = [press_other, release_other]
        elif eventType == "b2d":
            events = [press_other, release_other]
            click_type = double_click
        elif eventType == "b3p":
            events = [press_right]
            drag_button_remembered = drag_right
        elif eventType == "b3r":
            events = [release_right]
            drag_button_remembered = None
        elif eventType == "b3c":
            events = [press_right, release_right]
        elif eventType == "b3d":
            events = [press_right, release_right]
            click_type = double_click
        else:
            raise LdtpServerException(u"Mouse event '%s' not implemented" % eventType)

        for event in events:
            CG_event = CGEventCreateMouseEvent(None, event, point, button)
            if click_type:
                CGEventSetIntegerValueField(
                    CG_event, kCGMouseEventClickState, click_type)
            CGEventPost(kCGHIDEventTap, CG_event)
            # Give the event time to happen
            time.sleep(0.01)
        return 1

    def mousemove(self, window_name, object_name):
        """
        Mouse move on an object.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        raise LdtpServerException("Not implemented")

    def doubleclick(self, window_name, object_name):
        """
        Double click on the object
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        """
        object_handle = self._get_object_handle(window_name, object_name)
        if not object_handle.AXEnabled:
            raise LdtpServerException(u"Object %s state disabled" % object_name)
        self._grabfocus(object_handle)
        x, y, width, height = self._getobjectsize(object_handle)
        window=self._get_front_most_window()
        # Mouse double click on the object
        #object_handle.doubleClick()
        window.doubleClickMouse((x + width / 2, y + height / 2))
        return 1

    def simulatemousemove(self, source_x, source_y, dest_x, dest_y, delay = 0.0):
        """
        @param source_x: Source X
        @type source_x: integer
        @param source_y: Source Y
        @type source_y: integer
        @param dest_x: Dest X
        @type dest_x: integer
        @param dest_y: Dest Y
        @type dest_y: integer
        @param delay: Sleep time between the mouse move
        @type delay: double

        @return: 1 if simulation was successful, 0 if not.
        @rtype: integer
        """
        raise LdtpServerException("Not implemented")
