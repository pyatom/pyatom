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
 * axlib.h --
 *
 *      Header file for apple accessibility functions.
 */

#ifndef _AXLIB_H_
#define _AXLIB_H_

#include <ApplicationServices/ApplicationServices.h>
#include <sys/types.h>

/*
 * Global functions
 */

Boolean AXEnabled(void);
pid_t getFrontmostPID(void);
CFTypeRef getFrontMostWindowTitle(pid_t pid);

#endif // ifndef _AXLIB_H_
