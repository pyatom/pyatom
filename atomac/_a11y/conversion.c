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
 *      Convert a CG value (CGSize or CGPoint) to Python tuple
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
   int val1 = 0;
   int val2 = 0;
   PyObject *tuple = PyTuple_New(2);

   if (kAXValueCGSizeType == AXValueGetType(value)) {
      CGSize size;
      if (AXValueGetValue(value,kAXValueCGSizeType,&size) == 0){
		 return NULL;
      }
	  val1 = size.width;
	  val2 = size.height;
   }

   if (kAXValueCGPointType == AXValueGetType(value)){
      CGPoint point;
      if (AXValueGetValue(value,kAXValueCGPointType,&point) == 0){
		 return NULL;
      }
	  val1 = point.x;
	  val2 = point.y;
   }

   PyTuple_SetItem(tuple,0,Py_BuildValue("i",val1));
   PyTuple_SetItem(tuple,1,Py_BuildValue("i",val2));
   return tuple;
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
