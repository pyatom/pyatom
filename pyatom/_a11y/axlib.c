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
 * axlib.c --
 *
 *      Library of Apple accessibility functions used in ATOMac
 */

#include "axlib.h"

/*
 *-----------------------------------------------------------------------------
 *
 * AXEnabled --
 *
 *      Determine whether a11y is enabled or not.
 *
 * Results:
 *      TRUE if enabled, FALSE if not.
 *
 * Side effects:
 *      None.
 *
 *-----------------------------------------------------------------------------
 */

Boolean
AXEnabled(void)
{
   if (AXAPIEnabled() != 0) {
      return TRUE;
   } else {
      return FALSE;
   }
}

/*
 *-----------------------------------------------------------------------------
 *
 * getFrontmostPID --
 *
 *      Get the PID of the front most (active) window from a11y
 *
 * Results:
 *      PID of the front most process.
 *
 * Side effects:
 *      None.
 *
 *-----------------------------------------------------------------------------
 */

pid_t
getFrontmostPID(void)
{
   pid_t pid;
   ProcessSerialNumber psn;

   GetFrontProcess(&psn);
   GetProcessPID(&psn, &pid);

   return pid;
}

/*
 *-----------------------------------------------------------------------------
 *
 * getFrontMostWindowTitle --
 *
 *      Function to get the title of the frontmost window of an app.
 *      Deprecated - for demo only. See notes in a11ymodule.c.
 *
 * Results:
 *      CFStringRef pointing to the title of the window.
 *
 * Side effects:
 *      None.
 *
 *-----------------------------------------------------------------------------
 */

CFTypeRef
getFrontMostWindowTitle(pid_t pid)
{
   AXUIElementRef app;
   CFTypeRef windowTitle;
   CFTypeRef temp;

   app = AXUIElementCreateApplication(pid);
   // check for nulls
   AXUIElementCopyAttributeValue(app, kAXFocusedWindowAttribute,
                                 (CFTypeRef *)&temp
                                 );
   AXUIElementCopyAttributeValue(
                                 temp, kAXTitleAttribute, (CFTypeRef *)&windowTitle
                                 );

   return windowTitle;
}
