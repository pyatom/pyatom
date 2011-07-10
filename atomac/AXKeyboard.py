# Copyright (c) 2010 VMware, Inc. All Rights Reserved.

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

import Quartz

from AXKeyCodeConstants import *


# Based on the flags provided in the Quartz documentation it does not seem
# that we can distinguish between left and right modifier keys, even though
# there are different virtual key codes offered between the two sets.
# Thus for now we offer only a generic modifier key set w/o L-R distinction.
modKeyFlagConstants = {
                         COMMAND:    Quartz.kCGEventFlagMaskCommand,
                         SHIFT:      Quartz.kCGEventFlagMaskShift,
                         OPTION:     Quartz.kCGEventFlagMaskAlternate,
                         CONTROL:    Quartz.kCGEventFlagMaskControl,
                      }


def loadKeyboard():
   ''' Load a given keyboard mapping (of characters to virtual key codes)

       Default is US keyboard
       Parameters: None (relies on the internationalization settings)
       Returns: A dictionary representing the current keyboard mapping (of
                characters to keycodes)
   '''
   # Currently assumes US keyboard
   keyboardLayout = {}
   keyboardLayout = DEFAULT_KEYBOARD
   keyboardLayout.update(specialKeys)

   return keyboardLayout
