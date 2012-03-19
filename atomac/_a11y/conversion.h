/* **********************************************************
 * Copyright 2010 VMware, Inc.  All rights reserved.
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
 * conversion.h --
 *
 *      Header file for CF to Python conversion library.
 */

#ifndef _CONVERSION_H_
#define _CONVERSION_H_

#include <Python.h>
#include <ApplicationServices/ApplicationServices.h>
/*
 * Global constants
 */

/*
 * Let's standardize on UTF-8 as the intermediate format for strings.
 */
static const CFStringEncoding CFENCODING = kCFStringEncodingUTF8;

/*
 * Global functions
 */

PyObject * CFStringRefToPyUnicode (CFStringRef source);
CFStringRef PyUnicodeToCFStringRef(PyObject * source);
PyObject * CGValueToPyTuple(AXValueRef value);

#endif // ifndef _CONVERSION_H_
