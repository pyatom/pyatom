/* **********************************************************
 * Copyright (C) 2010 VMware, Inc. All rights reserved.
 * **********************************************************/

/* **************************************************************************
 * This file is part of ATOMac.
 *
 * ATOMac is free software; you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free
 * Software Foundation version 2 and no later version.
 *
 * ATOMac is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. See the GNU General Public License version 2
 * for more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * this program; if not, write to the Free Software Foundation, Inc., 51
 * Franklin St, Fifth Floor, Boston, MA 02110-1301 USA.
 * **************************************************************************/

/*
 * conversion.c --
 *
 *      Functions to convert between Apple CoreFoundation objects and
 *      Python objects.
 */


#include "conversion.h"

/*
 * Local data
 */

/*
 * A note on ownership:
 *
 * Python and CF both have a notion of ownership. These functions convert from
 * type A to type B but do not touch ownership. So, if you pass in a CF string
 * and get a Python string back, you still own the CF string and ownership of
 * the Python string is given to you. You will need to account for this
 * somehow. Ownership should be documented in "side effects." Good luck!
 */

/*
 *-----------------------------------------------------------------------------
 *
 * CFStringRefToPyUnicode --
 *
 *      Convert an Apple CFString to a Python Unicode object
 *
 * Results:
 *      Returns a Python Unicode string or NULL and a Python exception on
 *      failure.
 *
 * Side effects:
 *      Ownership of the Python string object is transferred to the caller.
 *      Ownership of the CFString is unchanged.
 *
 *-----------------------------------------------------------------------------
 */

PyObject *
CFStringRefToPyUnicode(CFStringRef source) // IN: CFString to convert
{
   CFIndex buf_size;
   Boolean result;
   char *dest;
   PyObject *ret;

   buf_size = CFStringGetMaximumSizeForEncoding(
                                                CFStringGetLength(source),
                                                CFENCODING
                                                ) + 1;
   dest = (char *) PyMem_Malloc(buf_size);
   if (NULL == dest) {
      return NULL;
   }

   result = CFStringGetCString(source, dest, buf_size, CFENCODING);
   if (FALSE == result) {
      PyErr_SetString(PyExc_ValueError,
                      "Error converting CFString to C string");
      return NULL;
   }
   ret = PyUnicode_DecodeUTF8(dest, strlen(dest), NULL);
   PyMem_Free(dest);
   return ret;
}

/*
 *-----------------------------------------------------------------------------
 *
 * CGValueToPyTuple --
 *
 *      Convert a CG value (CGSize, CGPoint, or CFRange) to Python tuple
 *
 * Results:
 *      Returns a Python Tuple or NULL and a Python exception on
 *      failure.
 *
 * Side effects:
 *      Ownership of the Python Tuple object is transferred to the caller.
 *
 *-----------------------------------------------------------------------------
 */

PyObject *
CGValueToPyTuple(AXValueRef value) //IN: AXValueRef to convert
{
   PyObject *tuple = PyTuple_New(2);

   if (kAXValueCGSizeType == AXValueGetType(value)) {
      CGSize size;
      double float1 = 0.0;
      double float2 = 0.0;
      if (AXValueGetValue(value,kAXValueCGSizeType,&size) == 0){
       return NULL;
      }
      float1 = (double)size.width;
      float2 = (double)size.height;
      PyTuple_SetItem(tuple,0,Py_BuildValue("d",float1));
      PyTuple_SetItem(tuple,1,Py_BuildValue("d",float2));
      return tuple;
   }

   if (kAXValueCGPointType == AXValueGetType(value)){
      CGPoint point;
      double float1 = 0.0;
      double float2 = 0.0;
      if (AXValueGetValue(value,kAXValueCGPointType,&point) == 0){
       return NULL;
      }
      float1 = (double)point.x;
      float2 = (double)point.y;
      PyTuple_SetItem(tuple,0,Py_BuildValue("d",float1));
      PyTuple_SetItem(tuple,1,Py_BuildValue("d",float2));
      return tuple;
   }

   if (kAXValueCFRangeType == AXValueGetType(value)){
      CFRange range;
      long index1 = 0;
      long index2 = 0;
      if (AXValueGetValue(value,kAXValueCFRangeType,&range) == 0){
       return NULL;
      }
      index1 = range.location;
      index2 = range.length;
      PyTuple_SetItem(tuple,0,Py_BuildValue("l",index1));
      PyTuple_SetItem(tuple,1,Py_BuildValue("l",index2));
      return tuple;
   }

   // @@@TODO: Need to set a python exception here if not already set
   return NULL;
}

/*
 *-----------------------------------------------------------------------------
 *
 * PyUnicodeToCFStringRef --
 *
 *      Convert a Python Unicode object to an Apple CFString
 *
 * Results:
 *      Returns an Apple CFStringRef or NULL and a Python exception on
 *      failure.
 *
 * Side effects:
 *      Ownership of the CFString is given to the caller.
 *      Ownership of the Python string object is unchanged.
 *
 *-----------------------------------------------------------------------------
 */

CFStringRef
PyUnicodeToCFStringRef(PyObject * source) // IN: Python string object
{
   char *dest;
   PyObject *decoded;
   CFStringRef ret;

   if (PyUnicode_Check(source)) {
      decoded = PyUnicode_AsUTF8String(source);
      if (NULL == decoded) {
         return NULL;
      }
      dest = (char *) PyString_AsString(decoded); // dest is read-only here
      if (NULL == dest) {
         return NULL;
      }
   } else {
      dest = (char *) PyString_AsString(source);
      if (NULL == dest) {
         return NULL;
      }
   }

   ret = CFStringCreateWithCString(NULL, dest, CFENCODING);
   if (NULL == ret)
   {
      PyErr_SetString(PyExc_ValueError,
                      "Error creating CFString from C string");
      return NULL;
   }
   return ret;
}
