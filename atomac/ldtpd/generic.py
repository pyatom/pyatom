# Copyright (c) 2012 VMware, Inc. All Rights Reserved.

# This file is part of ATOMac.

#@author: Yingjun Li <yingjunli@gmail.com>                                                                                                      
#@copyright: Copyright (c) 2009-12 Yingjun Li                                                                                                  

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
"""Generic class."""

import os
import tempfile
from base64 import b64encode
from AppKit import *
from Quartz.CoreGraphics import *

from utils import Utils
from server_exception import LdtpServerException

class Generic(Utils):
    def imagecapture(self, window_name = None, x = 0, y = 0,
                     width = None, height = None):
        """
        Captures screenshot of the whole desktop or given window
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param x: x co-ordinate value
        @type x: int
        @param y: y co-ordinate value
        @type y: int
        @param width: width co-ordinate value
        @type width: int
        @param height: height co-ordinate value
        @type height: int

        @return: screenshot with base64 encoded for the client
        @rtype: string
        """
        if x or y or (width and width != -1) or (height and height != -1):
            raise LdtpServerException("Not implemented")
        if window_name:
            handle, name, app=self._get_window_handle(window_name)
            try:
                self._grabfocus(handle)
            except:
                pass
            rect = self._getobjectsize(handle)
            screenshot = CGWindowListCreateImage(NSMakeRect(rect[0],
                rect[1], rect[2], rect[3]), 1, 0, 0)
        else:
            screenshot = CGWindowListCreateImage(CGRectInfinite, 1, 0, 0)
        image = CIImage.imageWithCGImage_(screenshot)
        bitmapRep = NSBitmapImageRep.alloc().initWithCIImage_(image)
        blob = bitmapRep.representationUsingType_properties_(NSPNGFileType, None)
        tmpFile = tempfile.mktemp('.png', 'ldtpd_')
        blob.writeToFile_atomically_(tmpFile, False)
        rv = b64encode(open(tmpFile).read())
        os.remove(tmpFile)
        return rv

