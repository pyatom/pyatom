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
"""KeyboardOp class."""

import time
from atomac.AXClasses import NativeUIElement
from atomac.AXKeyCodeConstants import *
from server_exception import LdtpServerException

class KeyCombo:
  def __init__(self):
    self.modifiers=False
    self.value=''
    self.modVal=None

class KeyboardOp:
  def __init__(self):
    self._undefined_key=None
    self._max_tokens=256
    self._max_tok_size=15

  def _get_key_value(self, keyval):
    return_val=KeyCombo()
    if keyval == "command":
      keyval="command_l"
    elif keyval == "option" or keyval == "alt" or keyval == "alt_l":
      keyval="option_l"
    elif keyval == "alt_r":
      keyval="option_r"
    elif keyval == "control" or keyval == "ctrl" or keyval == "ctrl_l":
      keyval="control_l"
    elif keyval == "ctrl_r":
      keyval="control_r"
    elif keyval == "shift":
      keyval="shift_l"
    elif keyval == "left":
      keyval="cursor_left"
    elif keyval == "right":
      keyval="cursor_right"
    elif keyval == "up":
      keyval="cursor_up"
    elif keyval == "down":
      keyval="cursor_down"
    elif keyval == "bksp":
      keyval="backspace"
    elif keyval == "enter":
      keyval="return"
    elif keyval == "pgdown":
      keyval="page_down"
    elif keyval == "pagedown":
      keyval="page_down"
    elif keyval == "pgup":
      keyval="page_up"
    elif keyval == "pageup":
      keyval="page_up"
    elif keyval == "esc":
      keyval="escape"
    key="<%s>" % keyval
    # This will identify Modifiers
    if key in ["<command_l>", "<command_r>",
               "<shift_l>", "<shift_r>",
               "<control_l>", "<control_r>",
               "<option_l>", "<option_r>"]:
        return_val.modifiers=True
        return_val.modVal=[key]
        return return_val
    # This will identify all US_keyboard characters
    if keyval.lower() in US_keyboard:
        return_val.value=keyval
        return return_val
    # This will identify all specialKeys
    if key in specialKeys:
        return_val.value=key
        return return_val
    # Key Undefined
    return return_val

  def get_keyval_id(self, input_str):
    index=0
    key_vals=[]
    lastModifiers=None
    while index  < len(input_str):
      token=''
      # Identified a Non Printing Key
      if input_str[index] == '<':
        index += 1
        i=0
        while input_str[index] != '>' and i < self._max_tok_size:
          token += input_str[index]
          index += 1
          i += 1
        if input_str[index] != '>':
          # Premature end of string without an opening '<'
          return None
        index += 1
      else:
        token=input_str[index]
        index += 1

      key_val=self._get_key_value(token)
      # Deal with modifier and undefined keys.
      # Modifiers: if we got modifier in previous
      # step, extend the previous KeyCombo object instead
      # of creating a new one.
      if lastModifiers and key_val.value != self._undefined_key:
        last_item = key_vals.pop()
        if key_val.modifiers:
          lastModifiers = key_val
          last_item.modVal.extend(key_val.modVal)
          key_val = last_item
        else:
          last_item.value = key_val.value
          key_val = last_item
          lastModifiers=None
      elif key_val.modifiers:
        if not lastModifiers:
          lastModifiers=key_val
        else:
          last_item=key_vals.pop()
          last_item.modVal.extend(key_val.modVal)
          key_val=last_item
      elif key_val.value == self._undefined_key:
        # Invalid key
        return None
      key_vals.append(key_val)
    return key_vals

class KeyComboAction:
    """Used for sending keyboard events to the system."""

    def __init__(self, data):
        """
        @param data: data to type
        @type data: string
        """
        self._data=data
        # Create dummy window, it has code for creating and queuing events.
        # We will send events 'globally' to the system so dummy window will
        # not receive the event.
        self._dummy_window=NativeUIElement()
        _keyOp=KeyboardOp()
        self._keyvalId=_keyOp.get_keyval_id(data)
        if not self._keyvalId:
          raise LdtpServerException("Unsupported keys passed")
        self._doCombo()

    def _doCombo(self):
        for key_val in self._keyvalId:
            if key_val.modifiers:
              self._dummy_window.sendGlobalKeyWithModifiers(key_val.value,
                                                            key_val.modVal)
            else:
              self._dummy_window.sendGlobalKey(key_val.value)
            time.sleep(0.01)

class KeyPressAction:
    def __init__(self, window, data):
        self._data=data
        self._window=window
        _keyOp=KeyboardOp()
        self._keyvalId=_keyOp.get_keyval_id(data)
        if not self._keyvalId:
          raise LdtpServerException("Unsupported keys passed")
        self._doPress()

    def _doPress(self):
       for key_val in self._keyvalId:
          if key_val.modifiers:
             self._window.pressModifiers(key_val.modVal)
          else:
             raise LdtpServerException("Unsupported modifiers")
          time.sleep(0.01)

class KeyReleaseAction:
    def __init__(self, window, data):
        self._data=data
        self._window=window
        _keyOp=KeyboardOp()
        self._keyvalId=_keyOp.get_keyval_id(data)
        if not self._keyvalId:
            raise LdtpServerException("Unsupported keys passed")
        self._doRelease()

    def _doRelease(self):
       for key_val in self._keyvalId:
          if key_val.modifiers:
             self._window.releaseModifiers(key_val.modVal)
          else:
             raise LdtpServerException("Unsupported modifiers")
          time.sleep(0.01)
