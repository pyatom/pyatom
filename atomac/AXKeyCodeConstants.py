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

# Special keys
TAB            = '<tab>'
RETURN         = '<return>'
ESCAPE         = '<escape>'
CAPS_LOCK      = '<capslock>'
DELETE         = '<delete>'
NUM_LOCK       = '<num_lock>'
SCROLL_LOCK    = '<scroll_lock>'
PAUSE          = '<pause>'
BACKSPACE      = '<backspace>'
INSERT         = '<insert>'

# Cursor movement
UP             = '<cursor_up>'
DOWN           = '<cursor_down>'
LEFT           = '<cursor_left>'
RIGHT          = '<cursor_right>'
PAGE_UP        = '<page_up>'
PAGE_DOWN      = '<page_down>'
HOME           = '<home>'
END            = '<end>'

# Numeric keypad
NUM_0          = '<num_0>'
NUM_1          = '<num_1>'
NUM_2          = '<num_2>'
NUM_3          = '<num_3>'
NUM_4          = '<num_4>'
NUM_5          = '<num_5>'
NUM_6          = '<num_6>'
NUM_7          = '<num_7>'
NUM_8          = '<num_8>'
NUM_9          = '<num_9>'
NUM_ENTER      = '<num_enter>'
NUM_PERIOD     = '<num_.>'
NUM_PLUS       = '<num_+>'
NUM_MINUS      = '<num_->'
NUM_MULTIPLY   = '<num_*>'
NUM_DIVIDE     = '<num_/>'

# Function keys
F1             = '<f1>'
F2             = '<f2>'
F3             = '<f3>'
F4             = '<f4>'
F5             = '<f5>'
F6             = '<f6>'
F7             = '<f7>'
F8             = '<f8>'
F9             = '<f9>'
F10            = '<f10>'
F11            = '<f11>'
F12            = '<f12>'

# Modifier keys
COMMAND_L      = '<command_l>'
SHIFT_L        = '<shift_l>'
OPTION_L       = '<option_l>'
CONTROL_L      = '<control_l>'

COMMAND_R      = '<command_r>'
SHIFT_R        = '<shift_r>'
OPTION_R       = '<option_r>'
CONTROL_R      = '<control_r>'

# Default modifier keys -> left:
COMMAND        = COMMAND_L
SHIFT          = SHIFT_L
OPTION         = OPTION_L
CONTROL        = CONTROL_L


# Define a dictionary representing characters mapped to their virtual key codes
# Lifted from the mappings found in kbdptr.h in the osxvnc project
# Mapping is: character -> virtual keycode for each character / symbol / key
# as noted below

US_keyboard = {
                 # Letters
                 'a':  0,
                 'b':  11,
                 'c':  8,
                 'd':  2,
                 'e':  14,
                 'f':  3,
                 'g':  5,
                 'h':  4,
                 'i':  34,
                 'j':  38,
                 'k':  40,
                 'l':  37,
                 'm':  46,
                 'n':  45,
                 'o':  31,
                 'p':  35,
                 'q':  12,
                 'r':  15,
                 's':  1,
                 't':  17,
                 'u':  32,
                 'v':  9,
                 'w':  13,
                 'x':  7,
                 'y':  16,
                 'z':  6,

                 # Numbers
                 '0':  29,
                 '1':  18,
                 '2':  19,
                 '3':  20,
                 '4':  21,
                 '5':  23,
                 '6':  22,
                 '7':  26,
                 '8':  28,
                 '9':  25,

                 # Symbols
                 '!':  18,
                 '@':  19,
                 '#':  20,
                 '$':  21,
                 '%':  23,
                 '^':  22,
                 '&':  26,
                 '*':  28,
                 '(':  25,
                 ')':  29,
                 '-':  27,        # Dash
                 '_':  27,        # Underscore
                 '=':  24,
                 '+':  24,
                 '`':  50,        # Backtick
                 '~':  50,
                 '[':  33,
                 ']':  30,
                 '{':  33,
                 '}':  30,
                 ';':  41,
                 ':':  41,
                 "'":  39,
                 '"':  39,
                 ',':  43,
                 '<':  43,
                 '.':  47,
                 '>':  47,
                 '/':  44,
                 '?':  44,
                 '\\': 42,
                 '|':  42,        # Pipe
                 TAB:  48,        # Tab: Shift-Tab sent for Tab
                 ' ':  49,        # Space

                 # Characters that on the US keyboard require use with Shift
                 'upperSymbols': [
                                     '!',
                                     '@',
                                     '#',
                                     '$',
                                     '%',
                                     '^',
                                     '&',
                                     '*',
                                     '(',
                                     ')',
                                     '_',
                                     '+',
                                     '~',
                                     '{',
                                     '}',
                                     ':',
                                     '"',
                                     '<',
                                     '>',
                                     '?',
                                     '|',
                                 ]
             }


# Mapping for special (meta) keys
specialKeys = {
                 # Special keys
                 RETURN:           36,
                 DELETE:           117,
                 TAB:              48,
                 ESCAPE:           53,
                 CAPS_LOCK:        57,
                 NUM_LOCK:         71,
                 SCROLL_LOCK:      107,
                 PAUSE:            113,
                 BACKSPACE:        51,
                 INSERT:           114,

                 # Cursor movement
                 UP:               126,
                 DOWN:             125,
                 LEFT:             123,
                 RIGHT:            124,
                 PAGE_UP:          116,
                 PAGE_DOWN:        121,

                 # Numeric keypad
                 NUM_0:            82,
                 NUM_1:            83,
                 NUM_2:            84,
                 NUM_3:            85,
                 NUM_4:            86,
                 NUM_5:            87,
                 NUM_6:            88,
                 NUM_7:            89,
                 NUM_8:            91,
                 NUM_9:            92,
                 NUM_ENTER:        76,
                 NUM_PERIOD:       65,
                 NUM_PLUS:         69,
                 NUM_MINUS:        78,
                 NUM_MULTIPLY:     67,
                 NUM_DIVIDE:       75,

                 # Function keys
                 F1:               122,
                 F2:               120,
                 F3:               99,
                 F4:               118,
                 F5:               96,
                 F6:               97,
                 F7:               98,
                 F8:               100,
                 F9:               101,
                 F10:              109,
                 F11:              103,
                 F12:              111,

                  # Modifier keys
                 COMMAND_L:        55,
                 SHIFT_L:          56,
                 OPTION_L:         58,
                 CONTROL_L:        59,

                 COMMAND_R:        54,
                 SHIFT_R:          60,
                 OPTION_R:         61,
                 CONTROL_R:        62,
              }

# Default keyboard layout
DEFAULT_KEYBOARD = US_keyboard
