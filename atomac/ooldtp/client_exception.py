# Copyright (c) 2012 VMware, Inc. All Rights Reserved.

# This file is part of ATOMac.

#@author: Eitan Isaacson <eitan@ascender.com>
#@author: Nagappan Alagappan <nagappan@gmail.com>
#@copyright: Copyright (c) 2009 Eitan Isaacson
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
"""Python LDTP exception"""

ERROR_CODE = 123

class LdtpExecutionError(Exception):
    pass
