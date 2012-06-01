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
import atomac
import fnmatch

from utils import Utils
from server_exception import LdtpServerException

class ComboBox(Utils):
    def selectitem(self, window_name, object_name, item_name):
        object_handle = self._get_object_handle(window_name, object_name)
        if not object_handle:
            raise LdtpServerException(u"Unable to find object %s" % object_name)
        object_handle.Press()
        object_handle = self._get_object_handle(window_name, item_name, 'AXMenuItem')
        if not object_handle:
            raise LdtpServerException(u"Unable to find item %s" % item_name)
        object_handle.Press()
        return 1

    # Since selectitem and comboselect implementation are same,
    # for Linux/Windows API compatibility let us assign selectitem to comboselect
    comboselect = selectitem
