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
"""Value class."""

import time

from utils import Utils
from server_exception import LdtpServerException

class Value(Utils):
   def verifyscrollbarvertical(self, window_name, object_name):
      """
      Verify scrollbar is vertical
      
      @param window_name: Window name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type window_name: string
      @param object_name: Object name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type object_name: string
      
      @return: 1 on success.
      @rtype: integer
      """
      try:
         object_handle = self._get_object_handle(window_name, object_name)
         if object_handle.AXOrientation == "AXVerticalOrientation":
            return 1
      except:
         pass
      return 0

   def verifyscrollbarhorizontal(self, window_name, object_name):
      """
      Verify scrollbar is horizontal
      
      @param window_name: Window name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type window_name: string
      @param object_name: Object name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type object_name: string
      
      @return: 1 on success.
      @rtype: integer
      """
      try:
         object_handle = self._get_object_handle(window_name, object_name)
         if object_handle.AXOrientation == "AXHorizontalOrientation":
            return 1
      except:
         pass
      return 0

   def setmax(self, window_name, object_name):
      """
      Set max value
      
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
      object_handle.AXValue = 1
      return 1
   
   def setmin(self, window_name, object_name):
      """
      Set min value
      
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
      object_handle.AXValue = 0
      return 1
   
   def scrollup(self, window_name, object_name):
      """
      Scroll up
      
      @param window_name: Window name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type window_name: string
      @param object_name: Object name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type object_name: string
      
      @return: 1 on success.
      @rtype: integer
      """
      if not self.verifyscrollbarvertical(window_name, object_name):
         raise LdtpServerException('Object not vertical scrollbar')
      return self.setmin(window_name, object_name)
   
   def scrolldown(self, window_name, object_name):
      """
      Scroll down
      
      @param window_name: Window name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type window_name: string
      @param object_name: Object name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type object_name: string
      
      @return: 1 on success.
      @rtype: integer
      """
      if not self.verifyscrollbarvertical(window_name, object_name):
         raise LdtpServerException('Object not vertical scrollbar')
      return self.setmax(window_name, object_name)

   def scrollleft(self, window_name, object_name):
      """
      Scroll left
      
      @param window_name: Window name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type window_name: string
      @param object_name: Object name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type object_name: string
      
      @return: 1 on success.
      @rtype: integer
      """
      if not self.verifyscrollbarhorizontal(window_name, object_name):
         raise LdtpServerException('Object not horizontal scrollbar')
      return self.setmin(window_name, object_name)
   
   def scrollright(self, window_name, object_name):
      """
      Scroll right
      
      @param window_name: Window name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type window_name: string
      @param object_name: Object name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type object_name: string
      
      @return: 1 on success.
      @rtype: integer
      """
      if not self.verifyscrollbarhorizontal(window_name, object_name):
         raise LdtpServerException('Object not horizontal scrollbar')
      return self.setmax(window_name, object_name)

   def onedown(self, window_name, object_name, iterations):
      """
      Press scrollbar down with number of iterations
      
      @param window_name: Window name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type window_name: string
      @param object_name: Object name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type object_name: string
      @param interations: iterations to perform on slider increase
      @type iterations: integer
      
      @return: 1 on success.
      @rtype: integer
      """
      if not self.verifyscrollbarvertical(window_name, object_name):
         raise LdtpServerException('Object not vertical scrollbar')
      object_handle = self._get_object_handle(window_name, object_name)
      i = 0
      maxValue = 1.0 / 8
      flag = False
      while i < iterations:
         if object_handle.AXValue >= 1:
            raise LdtpServerException('Maximum limit reached')
         object_handle.AXValue += maxValue
         time.sleep(1.0 / 100)
         flag = True
         i += 1
      if flag:
         return 1
      else:
         raise LdtpServerException('Unable to increase scrollbar')
   
   def oneup(self, window_name, object_name, iterations):
      """
      Press scrollbar up with number of iterations
      
      @param window_name: Window name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type window_name: string
      @param object_name: Object name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type object_name: string
      @param interations: iterations to perform on slider increase
      @type iterations: integer
      
      @return: 1 on success.
      @rtype: integer
      """
      if not self.verifyscrollbarvertical(window_name, object_name):
         raise LdtpServerException('Object not vertical scrollbar')
      object_handle = self._get_object_handle(window_name, object_name)
      i = 0
      minValue = 1.0 / 8
      flag = False
      while i < iterations:
         if object_handle.AXValue <= 0:
            raise LdtpServerException('Minimum limit reached')
         object_handle.AXValue -= minValue
         time.sleep(1.0 / 100)
         flag = True
         i += 1
      if flag:
         return 1
      else:
         raise LdtpServerException('Unable to decrease scrollbar')
      
   def oneright(self, window_name, object_name, iterations):
      """
      Press scrollbar right with number of iterations
      
      @param window_name: Window name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type window_name: string
      @param object_name: Object name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type object_name: string
      @param interations: iterations to perform on slider increase
      @type iterations: integer
      
      @return: 1 on success.
      @rtype: integer
      """
      if not self.verifyscrollbarhorizontal(window_name, object_name):
         raise LdtpServerException('Object not horizontal scrollbar')
      object_handle = self._get_object_handle(window_name, object_name)
      i = 0
      maxValue = 1.0 / 8
      flag = False
      while i < iterations:
         if object_handle.AXValue >= 1:
            raise LdtpServerException('Maximum limit reached')
         object_handle.AXValue += maxValue
         time.sleep(1.0 / 100)
         flag = True
         i += 1
      if flag:
         return 1
      else:
         raise LdtpServerException('Unable to increase scrollbar')

   def oneleft(self, window_name, object_name, iterations):
      """
      Press scrollbar left with number of iterations
      
      @param window_name: Window name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type window_name: string
      @param object_name: Object name to type in, either full name,
      LDTP's name convention, or a Unix glob.
      @type object_name: string
      @param interations: iterations to perform on slider increase
      @type iterations: integer
      
      @return: 1 on success.
      @rtype: integer
      """
      if not self.verifyscrollbarhorizontal(window_name, object_name):
         raise LdtpServerException('Object not horizontal scrollbar')
      object_handle = self._get_object_handle(window_name, object_name)
      i = 0
      minValue = 1.0 / 8
      flag = False
      while i < iterations:
         if object_handle.AXValue <= 0:
            raise LdtpServerException('Minimum limit reached')
         object_handle.AXValue -= minValue
         time.sleep(1.0 / 100)
         flag = True
         i += 1
      if flag:
         return 1
      else:
         raise LdtpServerException('Unable to decrease scrollbar')
