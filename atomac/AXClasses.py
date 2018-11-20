# Copyright (c) 2010-2011 VMware, Inc. All Rights Reserved.

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

import fnmatch
import time
from collections import deque

import AppKit
import Quartz
from AppKit import NSURL, NSString, NSDictionary, NSArray
from PyObjCTools import AppHelper

from . import _a11y
from . import AXKeyboard
from . import AXCallbacks
from . import AXKeyCodeConstants


class BaseAXUIElement(_a11y.AXUIElement):
    """Base class for UI elements. Implements four major things:

    1. Factory class methods for getAppRef and getSystemObject which
       properly instantiate the class.
    2. Generators and methods for finding objects for use in child classes.
    3. __getattribute__ call for invoking actions.
    4. waitFor utility based upon AX notifications.
    """

    @classmethod
    def _getRunningApps(cls):
        """Get a list of the running applications."""

        def runLoopAndExit():
            AppHelper.stopEventLoop()

        AppHelper.callLater(1, runLoopAndExit)
        AppHelper.runConsoleEventLoop()
        # Get a list of running applications
        ws = AppKit.NSWorkspace.sharedWorkspace()
        apps = ws.runningApplications()
        return apps

    @classmethod
    def getAppRefByPid(cls, pid):
        """Get the top level element for the application specified by pid."""
        return _a11y.getAppRefByPid(cls, pid)

    @classmethod
    def getAppRefByBundleId(cls, bundleId):
        """
        Get the top level element for the application with the specified
        bundle ID, such as com.vmware.fusion.
        """
        ra = AppKit.NSRunningApplication
        # return value (apps) is always an array. if there is a match it will
        # have an item, otherwise it won't.
        apps = ra.runningApplicationsWithBundleIdentifier_(bundleId)
        if len(apps) == 0:
            raise ValueError(('Specified bundle ID not found in '
                              'running apps: %s' % bundleId))
        pid = apps[0].processIdentifier()
        return cls.getAppRefByPid(pid)

    @classmethod
    def getAppRefByLocalizedName(cls, name):
        """Get the top level element for the application with the specified
        localized name, such as VMware Fusion.

        Wildcards are also allowed.
        """
        # Refresh the runningApplications list
        apps = cls._getRunningApps()
        for app in apps:
            if fnmatch.fnmatch(app.localizedName(), name):
                pid = app.processIdentifier()
                return cls.getAppRefByPid(pid)
        raise ValueError('Specified application not found in running apps.')

    @classmethod
    def getFrontmostApp(cls):
        """Get the current frontmost application.

        Raise a ValueError exception if no GUI applications are found.
        """
        # Refresh the runningApplications list
        apps = cls._getRunningApps()
        for app in apps:
            pid = app.processIdentifier()
            ref = cls.getAppRefByPid(pid)
            try:
                if ref.AXFrontmost:
                    return ref
            except (_a11y.ErrorUnsupported,
                    _a11y.ErrorCannotComplete,
                    _a11y.ErrorAPIDisabled,
                    _a11y.ErrorNotImplemented):
                # Some applications do not have an explicit GUI
                # and so will not have an AXFrontmost attribute
                # Trying to read attributes from Google Chrome Helper returns
                # ErrorAPIDisabled for some reason - opened radar bug 12837995
                pass
        raise ValueError('No GUI application found.')

    @classmethod
    def getAnyAppWithWindow(cls):
        """Get a random app that has windows.

        Raise a ValueError exception if no GUI applications are found.
        """
        # Refresh the runningApplications list
        apps = cls._getRunningApps()
        for app in apps:
            pid = app.processIdentifier()
            ref = cls.getAppRefByPid(pid)
            if hasattr(ref, 'windows') and len(ref.windows()) > 0:
                return ref
        raise ValueError('No GUI application found.')

    @classmethod
    def getSystemObject(cls):
        """Get the top level system accessibility object."""
        return _a11y.getSystemObject(cls)

    @classmethod
    def setSystemWideTimeout(cls, timeout=0.0):
        """Set the system-wide accessibility timeout.

        Optional: timeout (non-negative float; defaults to 0)
                  A value of 0 will reset the timeout to the system default.
        Returns: None.
        """
        return cls.getSystemObject().setTimeout(timeout)

    @staticmethod
    def launchAppByBundleId(bundleID):
        """Launch the application with the specified bundle ID"""
        # NSWorkspaceLaunchAllowingClassicStartup does nothing on any
        # modern system that doesn't have the classic environment installed.
        # Encountered a bug when passing 0 for no options on 10.6 PyObjC.
        ws = AppKit.NSWorkspace.sharedWorkspace()
        # Sorry about the length of the following line
        r = ws.launchAppWithBundleIdentifier_options_additionalEventParamDescriptor_launchIdentifier_(
            bundleID,
            AppKit.NSWorkspaceLaunchAllowingClassicStartup,
            AppKit.NSAppleEventDescriptor.nullDescriptor(),
            None)
        # On 10.6, this returns a tuple - first element bool result, second is
        # a number. Let's use the bool result.
        if not r[0]:
            raise RuntimeError('Error launching specified application.')

    @staticmethod
    def launchAppByBundlePath(bundlePath, arguments=None):
        """Launch app with a given bundle path.

        Return True if succeed.
        """
        if arguments is None:
            arguments = []

        bundleUrl = NSURL.fileURLWithPath_(bundlePath)
        workspace = AppKit.NSWorkspace.sharedWorkspace()
        configuration = {
            AppKit.NSWorkspaceLaunchConfigurationArguments: arguments
        }

        return workspace.launchApplicationAtURL_options_configuration_error_(
            bundleUrl,
            AppKit.NSWorkspaceLaunchAllowingClassicStartup,
            configuration,
            None)

    @staticmethod
    def terminateAppByBundleId(bundleID):
        """Terminate app with a given bundle ID.
        Requires 10.6.

        Return True if succeed.
        """
        ra = AppKit.NSRunningApplication
        if getattr(ra, "runningApplicationsWithBundleIdentifier_"):
            appList = ra.runningApplicationsWithBundleIdentifier_(bundleID)
            if appList and len(appList) > 0:
                app = appList[0]
                return app and app.terminate() and True or False
        return False

    def setTimeout(self, timeout=0.0):
        """Set the accessibiltiy API timeout on the given reference.

        Optional: timeout (non-negative float; defaults to 0)
                  A value of 0 will reset the timeout to the system-wide
                  value
        Returns: None
        """
        self._setTimeout(timeout)

    def _postQueuedEvents(self, interval=0.01):
        """Private method to post queued events (e.g. Quartz events).

        Each event in queue is a tuple (event call, args to event call).
        """
        while len(self.eventList) > 0:
            (nextEvent, args) = self.eventList.popleft()
            nextEvent(*args)
            time.sleep(interval)

    def _clearEventQueue(self):
        """Clear the event queue."""
        if hasattr(self, 'eventList'):
            self.eventList.clear()

    def _queueEvent(self, event, args):
        """Private method to queue events to run.

        Each event in queue is a tuple (event call, args to event call).
        """
        if not hasattr(self, 'eventList'):
            self.eventList = deque([(event, args)])
            return
        self.eventList.append((event, args))

    def _addKeyToQueue(self, keychr, modFlags=0, globally=False):
        """Add keypress to queue.

        Parameters: key character or constant referring to a non-alpha-numeric
                    key (e.g. RETURN or TAB)
                    modifiers
                    global or app specific
        Returns: None or raise ValueError exception.
        """
        # Awkward, but makes modifier-key-only combinations possible
        # (since sendKeyWithModifiers() calls this)
        if not keychr:
            return

        if not hasattr(self, 'keyboard'):
            self.keyboard = AXKeyboard.loadKeyboard()

        if keychr in self.keyboard['upperSymbols'] and not modFlags:
            self._sendKeyWithModifiers(keychr,
                                       [AXKeyCodeConstants.SHIFT],
                                       globally)
            return

        if keychr.isupper() and not modFlags:
            self._sendKeyWithModifiers(
                keychr.lower(),
                [AXKeyCodeConstants.SHIFT],
                globally
            )
            return

        if keychr not in self.keyboard:
            self._clearEventQueue()
            raise ValueError('Key %s not found in keyboard layout' % keychr)

        # Press the key
        keyDown = Quartz.CGEventCreateKeyboardEvent(None,
                                                    self.keyboard[keychr],
                                                    True)
        # Release the key
        keyUp = Quartz.CGEventCreateKeyboardEvent(None,
                                                  self.keyboard[keychr],
                                                  False)
        # Set modflags on keyDown (default None):
        Quartz.CGEventSetFlags(keyDown, modFlags)
        # Set modflags on keyUp:
        Quartz.CGEventSetFlags(keyUp, modFlags)

        # Post the event to the given app
        if not globally:
            self._queueEvent(Quartz.CGEventPostToPid, (self._getPid(), keyDown))
            self._queueEvent(Quartz.CGEventPostToPid, (self._getPid(), keyUp))
        else:
            self._queueEvent(Quartz.CGEventPost, (0, keyDown))
            self._queueEvent(Quartz.CGEventPost, (0, keyUp))

    def _sendKey(self, keychr, modFlags=0, globally=False):
        """Send one character with no modifiers.

        Parameters: key character or constant referring to a non-alpha-numeric
                    key (e.g. RETURN or TAB)
                    modifier flags,
                    global or app specific
        Returns: None or raise ValueError exception
        """
        escapedChrs = {
            '\n': AXKeyCodeConstants.RETURN,
            '\r': AXKeyCodeConstants.RETURN,
            '\t': AXKeyCodeConstants.TAB,
        }
        if keychr in escapedChrs:
            keychr = escapedChrs[keychr]

        self._addKeyToQueue(keychr, modFlags, globally=globally)
        self._postQueuedEvents()

    def _sendKeys(self, keystr):
        """Send a series of characters with no modifiers.

        Parameters: keystr
        Returns: None or raise ValueError exception
        """
        for nextChr in keystr:
            self._sendKey(nextChr)

    def _pressModifiers(self, modifiers, pressed=True, globally=False):
        """Press given modifiers (provided in list form).

        Parameters: modifiers list, global or app specific
        Optional: keypressed state (default is True (down))
        Returns: Unsigned int representing flags to set
        """
        if not isinstance(modifiers, list):
            raise TypeError('Please provide modifiers in list form')

        if not hasattr(self, 'keyboard'):
            self.keyboard = AXKeyboard.loadKeyboard()

        modFlags = 0

        # Press given modifiers
        for nextMod in modifiers:
            if nextMod not in self.keyboard:
                errStr = 'Key %s not found in keyboard layout'
                self._clearEventQueue()
                raise ValueError(errStr % self.keyboard[nextMod])
            modEvent = Quartz.CGEventCreateKeyboardEvent(
                Quartz.CGEventSourceCreate(0),
                self.keyboard[nextMod],
                pressed
            )
            if not pressed:
                # Clear the modflags:
                Quartz.CGEventSetFlags(modEvent, 0)
            if globally:
                self._queueEvent(Quartz.CGEventPost, (0, modEvent))
            else:
                self._queueEvent(Quartz.CGEventPostToPid, (self._getPid(), modEvent))

            # Add the modifier flags
            modFlags += AXKeyboard.modKeyFlagConstants[nextMod]

        return modFlags

    def _holdModifierKeys(self, modifiers):
        """Hold given modifier keys (provided in list form).

        Parameters: modifiers list
        Returns: Unsigned int representing flags to set
        """
        modFlags = self._pressModifiers(modifiers)
        # Post the queued keypresses:
        self._postQueuedEvents()
        return modFlags

    def _releaseModifiers(self, modifiers, globally=False):
        """Release given modifiers (provided in list form).

        Parameters: modifiers list
        Returns: None
        """
        # Release them in reverse order from pressing them:
        modifiers.reverse()
        modFlags = self._pressModifiers(modifiers, pressed=False,
                                        globally=globally)
        return modFlags

    def _releaseModifierKeys(self, modifiers):
        """Release given modifier keys (provided in list form).

        Parameters: modifiers list
        Returns: Unsigned int representing flags to set
        """
        modFlags = self._releaseModifiers(modifiers)
        # Post the queued keypresses:
        self._postQueuedEvents()
        return modFlags

    @staticmethod
    def _isSingleCharacter(keychr):
        """Check whether given keyboard character is a single character.

        Parameters: key character which will be checked.
        Returns: True when given key character is a single character.
        """
        if not keychr:
            return False
        # Regular character case.
        if len(keychr) == 1:
            return True
        # Tagged character case.
        return keychr.count('<') == 1 and keychr.count('>') == 1 and \
               keychr[0] == '<' and keychr[-1] == '>'

    def _sendKeyWithModifiers(self, keychr, modifiers, globally=False):
        """Send one character with the given modifiers pressed.

        Parameters: key character, list of modifiers, global or app specific
        Returns: None or raise ValueError exception
        """
        if not self._isSingleCharacter(keychr):
            raise ValueError('Please provide only one character to send')

        if not hasattr(self, 'keyboard'):
            self.keyboard = AXKeyboard.loadKeyboard()

        modFlags = self._pressModifiers(modifiers, globally=globally)

        # Press the non-modifier key
        self._sendKey(keychr, modFlags, globally=globally)

        # Release the modifiers
        self._releaseModifiers(modifiers, globally=globally)

        # Post the queued keypresses:
        self._postQueuedEvents()

    def _queueMouseButton(self, coord, mouseButton, modFlags, clickCount=1,
                          dest_coord=None):
        """Private method to handle generic mouse button clicking.

        Parameters: coord (x, y) to click, mouseButton (e.g.,
                    kCGMouseButtonLeft), modFlags set (int)
        Optional: clickCount (default 1; set to 2 for double-click; 3 for
                  triple-click on host)
        Returns: None
        """
        # For now allow only left and right mouse buttons:
        mouseButtons = {
            Quartz.kCGMouseButtonLeft: 'LeftMouse',
            Quartz.kCGMouseButtonRight: 'RightMouse',
        }
        if mouseButton not in mouseButtons:
            raise ValueError('Mouse button given not recognized')

        eventButtonDown = getattr(Quartz,
                                  'kCGEvent%sDown' % mouseButtons[mouseButton])
        eventButtonUp = getattr(Quartz,
                                'kCGEvent%sUp' % mouseButtons[mouseButton])
        eventButtonDragged = getattr(Quartz,
                                     'kCGEvent%sDragged' % mouseButtons[
                                         mouseButton])

        # Press the button
        buttonDown = Quartz.CGEventCreateMouseEvent(None,
                                                    eventButtonDown,
                                                    coord,
                                                    mouseButton)
        # Set modflags (default None) on button down:
        Quartz.CGEventSetFlags(buttonDown, modFlags)

        # Set the click count on button down:
        Quartz.CGEventSetIntegerValueField(buttonDown,
                                           Quartz.kCGMouseEventClickState,
                                           int(clickCount))

        if dest_coord:
            # Drag and release the button
            buttonDragged = Quartz.CGEventCreateMouseEvent(None,
                                                           eventButtonDragged,
                                                           dest_coord,
                                                           mouseButton)
            # Set modflags on the button dragged:
            Quartz.CGEventSetFlags(buttonDragged, modFlags)

            buttonUp = Quartz.CGEventCreateMouseEvent(None,
                                                      eventButtonUp,
                                                      dest_coord,
                                                      mouseButton)
        else:
            # Release the button
            buttonUp = Quartz.CGEventCreateMouseEvent(None,
                                                      eventButtonUp,
                                                      coord,
                                                      mouseButton)
        # Set modflags on the button up:
        Quartz.CGEventSetFlags(buttonUp, modFlags)

        # Set the click count on button up:
        Quartz.CGEventSetIntegerValueField(buttonUp,
                                           Quartz.kCGMouseEventClickState,
                                           int(clickCount))
        # Queue the events
        self._queueEvent(Quartz.CGEventPost,
                         (Quartz.kCGSessionEventTap, buttonDown))
        if dest_coord:
            self._queueEvent(Quartz.CGEventPost,
                             (Quartz.kCGHIDEventTap, buttonDragged))
        self._queueEvent(Quartz.CGEventPost,
                         (Quartz.kCGSessionEventTap, buttonUp))

    def _leftMouseDragged(self, stopCoord, strCoord, speed):
        """Private method to handle generic mouse left button dragging and
        dropping.

        Parameters: stopCoord(x,y) drop point
        Optional: strCoord (x, y) drag point, default (0,0) get current
                  mouse position
                  speed (int) 1 to unlimit, simulate mouse moving
                  action from some special requirement
        Returns: None
        """
        # Get current position as start point if strCoord not given
        if strCoord == (0, 0):
            loc = AppKit.NSEvent.mouseLocation()
            strCoord = (loc.x, Quartz.CGDisplayPixelsHigh(0) - loc.y)

        # Press left button down
        pressLeftButton = Quartz.CGEventCreateMouseEvent(
            None,
            Quartz.kCGEventLeftMouseDown,
            strCoord,
            Quartz.kCGMouseButtonLeft
        )
        # Queue the events
        Quartz.CGEventPost(Quartz.CoreGraphics.kCGHIDEventTap, pressLeftButton)
        # Wait for reponse of system, a fuzzy icon appears
        time.sleep(5)
        # Simulate mouse moving speed, k is slope
        speed = round(1 / float(speed), 2)
        xmoved = stopCoord[0] - strCoord[0]
        ymoved = stopCoord[1] - strCoord[1]
        if ymoved == 0:
            raise ValueError('Not support horizontal moving')
        else:
            k = abs(ymoved / xmoved)

        if xmoved != 0:
            for xpos in range(int(abs(xmoved))):
                if xmoved > 0 and ymoved > 0:
                    currcoord = (strCoord[0] + xpos, strCoord[1] + xpos * k)
                elif xmoved > 0 and ymoved < 0:
                    currcoord = (strCoord[0] + xpos, strCoord[1] - xpos * k)
                elif xmoved < 0 and ymoved < 0:
                    currcoord = (strCoord[0] - xpos, strCoord[1] - xpos * k)
                elif xmoved < 0 and ymoved > 0:
                    currcoord = (strCoord[0] - xpos, strCoord[1] + xpos * k)
                # Drag with left button
                dragLeftButton = Quartz.CGEventCreateMouseEvent(
                    None,
                    Quartz.kCGEventLeftMouseDragged,
                    currcoord,
                    Quartz.kCGMouseButtonLeft
                )
                Quartz.CGEventPost(Quartz.CoreGraphics.kCGHIDEventTap,
                                   dragLeftButton)
                # Wait for reponse of system
                time.sleep(speed)
        else:
            raise ValueError('Not support vertical moving')
        upLeftButton = Quartz.CGEventCreateMouseEvent(
            None,
            Quartz.kCGEventLeftMouseUp,
            stopCoord,
            Quartz.kCGMouseButtonLeft
        )
        # Wait for reponse of system, a plus icon appears
        time.sleep(5)
        # Up left button up
        Quartz.CGEventPost(Quartz.CoreGraphics.kCGHIDEventTap, upLeftButton)

    def _waitFor(self, timeout, notification, **kwargs):
        """Wait for a particular UI event to occur; this can be built
        upon in NativeUIElement for specific convenience methods.
        """
        callback = self._matchOther
        retelem = None
        callbackArgs = None
        callbackKwargs = None

        # Allow customization of the callback, though by default use the basic
        # _match() method
        if 'callback' in kwargs:
            callback = kwargs['callback']
            del kwargs['callback']

            # Deal with these only if callback is provided:
            if 'args' in kwargs:
                if not isinstance(kwargs['args'], tuple):
                    errStr = 'Notification callback args not given as a tuple'
                    raise TypeError(errStr)

                # If args are given, notification will pass back the returned
                # element in the first positional arg
                callbackArgs = kwargs['args']
                del kwargs['args']

            if 'kwargs' in kwargs:
                if not isinstance(kwargs['kwargs'], dict):
                    errStr = 'Notification callback kwargs not given as a dict'
                    raise TypeError(errStr)

                callbackKwargs = kwargs['kwargs']
                del kwargs['kwargs']
            # If kwargs are not given as a dictionary but individually listed
            # need to update the callbackKwargs dict with the remaining items in
            # kwargs
            if kwargs:
                if callbackKwargs:
                    callbackKwargs.update(kwargs)
                else:
                    callbackKwargs = kwargs
        else:
            callbackArgs = (retelem, )
            # Pass the kwargs to the default callback
            callbackKwargs = kwargs

        return self._setNotification(timeout, notification, callback,
                                     callbackArgs,
                                     callbackKwargs)

    def waitForFocusToMatchCriteria(self, timeout=10, **kwargs):
        """Convenience method to wait for focused element to change
        (to element matching kwargs criteria).

        Returns: Element or None

        """
        def _matchFocused(retelem, **kwargs):
          return retelem if retelem._match(**kwargs) else None

        retelem = None
        return self._waitFor(timeout, 'AXFocusedUIElementChanged',
                             callback=_matchFocused,
                             args=(retelem, ),
                             **kwargs)


    def _getActions(self):
        """Retrieve a list of actions supported by the object."""
        actions = _a11y.AXUIElement._getActions(self)
        # strip leading AX from actions - help distinguish them from attributes
        return [action[2:] for action in actions]

    def _performAction(self, action):
        """Perform the specified action."""
        _a11y.AXUIElement._performAction(self, 'AX%s' % action)

    def _generateChildren(self):
        """Generator which yields all AXChildren of the object."""
        try:
            children = self.AXChildren
        except _a11y.Error:
            return
        if children:
            for child in children:
                yield child

    def _generateChildrenR(self, target=None):
        """Generator which recursively yields all AXChildren of the object."""
        if target is None:
            target = self
        try:
            children = target.AXChildren
        except _a11y.Error:
            return
        if children:
            for child in children:
                yield child
                for c in self._generateChildrenR(child):
                    yield c

    def _match(self, **kwargs):
        """Method which indicates if the object matches specified criteria.

        Match accepts criteria as kwargs and looks them up on attributes.
        Actual matching is performed with fnmatch, so shell-like wildcards
        work within match strings. Examples:

        obj._match(AXTitle='Terminal*')
        obj._match(AXRole='TextField', AXRoleDescription='search text field')
        """
        for k in kwargs.keys():
            try:
                val = getattr(self, k)
            except _a11y.Error:
                return False
            # Not all values may be strings (e.g. size, position)
            if isinstance(val, str):
                if not fnmatch.fnmatch(val, kwargs[k]):
                    return False
            else:
                if val != kwargs[k]:
                    return False
        return True

    def _matchOther(self, obj, **kwargs):
        """Perform _match but on another object, not self."""
        if obj is not None:
            # Need to check that the returned UI element wasn't destroyed first:
            if self._findFirstR(**kwargs):
                return obj._match(**kwargs)
        return False

    def _generateFind(self, **kwargs):
        """Generator which yields matches on AXChildren."""
        for needle in self._generateChildren():
            if needle._match(**kwargs):
                yield needle

    def _generateFindR(self, **kwargs):
        """Generator which yields matches on AXChildren and their children."""
        for needle in self._generateChildrenR():
            if needle._match(**kwargs):
                yield needle

    def _findAll(self, **kwargs):
        """Return a list of all children that match the specified criteria."""
        result = []
        for item in self._generateFind(**kwargs):
            result.append(item)
        return result

    def _findAllR(self, **kwargs):
        """Return a list of all children (recursively) that match the specified
        criteria.
        """
        result = []
        for item in self._generateFindR(**kwargs):
            result.append(item)
        return result

    def _findFirst(self, **kwargs):
        """Return the first object that matches the criteria."""
        for item in self._generateFind(**kwargs):
            return item

    def _findFirstR(self, **kwargs):
        """Search recursively for the first object that matches the criteria."""
        for item in self._generateFindR(**kwargs):
            return item

    def _getApplication(self):
        """Get the base application UIElement.

        If the UIElement is a child of the application, it will try
        to get the AXParent until it reaches the top application level
        element.
        """
        app = self
        while True:
            try:
                app = app.AXParent
            except _a11y.ErrorUnsupported:
                break
        return app

    def _menuItem(self, menuitem, *args):
        """Return the specified menu item.

        Example - refer to items by name:

        app._menuItem(app.AXMenuBar, 'File', 'New').Press()
        app._menuItem(app.AXMenuBar, 'Edit', 'Insert', 'Line Break').Press()

        Refer to items by index:

        app._menuitem(app.AXMenuBar, 1, 0).Press()

        Refer to items by mix-n-match:

        app._menuitem(app.AXMenuBar, 1, 'About TextEdit').Press()
        """
        self._activate()
        for item in args:
            # If the item has an AXMenu as a child, navigate into it.
            # This seems like a silly abstraction added by apple's a11y api.
            if menuitem.AXChildren[0].AXRole == 'AXMenu':
                menuitem = menuitem.AXChildren[0]
            # Find AXMenuBarItems and AXMenuItems using a handy wildcard
            role = 'AXMenu*Item'
            try:
                menuitem = menuitem.AXChildren[int(item)]
            except ValueError:
                menuitem = menuitem.findFirst(AXRole='AXMenu*Item',
                                              AXTitle=item)
        return menuitem

    def _activate(self):
        """Activate the application (bringing menus and windows forward)."""
        ra = AppKit.NSRunningApplication
        app = ra.runningApplicationWithProcessIdentifier_(
            self._getPid())
        # NSApplicationActivateAllWindows | NSApplicationActivateIgnoringOtherApps
        # == 3 - PyObjC in 10.6 does not expose these constants though so I have
        # to use the int instead of the symbolic names
        app.activateWithOptions_(3)

    def _getBundleId(self):
        """Return the bundle ID of the application."""
        ra = AppKit.NSRunningApplication
        app = ra.runningApplicationWithProcessIdentifier_(
            self._getPid())
        return app.bundleIdentifier()

    def _getLocalizedName(self):
        """Return the localized name of the application."""
        return self._getApplication().AXTitle

    def __getattr__(self, name):
        """Handle attribute requests in several ways:

        1. If it starts with AX, it is probably an a11y attribute. Pass
           it to the handler in _a11y which will determine that for sure.
        2. See if the attribute is an action which can be invoked on the
           UIElement. If so, return a function that will invoke the attribute.
        """
        if name.startswith('AX'):
            try:
                attr = self._getAttribute(name)
                return attr
            except AttributeError:
                pass

        # Populate the list of callable actions:
        actions = []
        try:
            actions = self._getActions()
        except Exception:
            pass

        if name.startswith('AX') and (name[2:] in actions):
            errStr = 'Actions on an object should be called without AX ' \
                     'prepended'
            raise AttributeError(errStr)

        if name in actions:
            def performSpecifiedAction():
                # activate the app before performing the specified action
                self._activate()
                return self._performAction(name)

            return performSpecifiedAction
        else:
            raise AttributeError('Object %s has no attribute %s' % (self, name))

    def __setattr__(self, name, value):
        """Set attributes on the object."""
        if name.startswith('AX'):
            return self._setAttribute(name, value)
        else:
            _a11y.AXUIElement.__setattr__(self, name, value)

    def __repr__(self):
        """Build a descriptive string for UIElements."""
        title = repr('')
        role = '<No role!>'
        c = repr(self.__class__).partition('<class \'')[-1].rpartition('\'>')[0]
        try:
            title = repr(self.AXTitle)
        except Exception:
            try:
                title = repr(self.AXValue)
            except Exception:
                try:
                    title = repr(self.AXRoleDescription)
                except Exception:
                    pass
        try:
            role = self.AXRole
        except Exception:
            pass
        if len(title) > 20:
            title = title[:20] + '...\''
        return '<%s %s %s>' % (c, role, title)


class NativeUIElement(BaseAXUIElement):
    """NativeUIElement class - expose the accessibility API in the simplest,
    most natural way possible.
    """

    def getAttributes(self):
        """Get a list of the attributes available on the element."""
        return self._getAttributes()

    def getActions(self):
        """Return a list of the actions available on the element."""
        return self._getActions()

    def setString(self, attribute, string):
        """Set the specified attribute to the specified string."""
        return self._setString(attribute, string)

    def findFirst(self, **kwargs):
        """Return the first object that matches the criteria."""
        return self._findFirst(**kwargs)

    def findFirstR(self, **kwargs):
        """Search recursively for the first object that matches the
        criteria.
        """
        return self._findFirstR(**kwargs)

    def findAll(self, **kwargs):
        """Return a list of all children that match the specified criteria."""
        return self._findAll(**kwargs)

    def findAllR(self, **kwargs):
        """Return a list of all children (recursively) that match
        the specified criteria.
        """
        return self._findAllR(**kwargs)

    def getElementAtPosition(self, coord):
        """Return the AXUIElement at the given coordinates.

        If self is behind other windows, this function will return self.
        """
        return self._getElementAtPosition(float(coord[0]), float(coord[1]))

    def activate(self):
        """Activate the application (bringing menus and windows forward)"""
        return self._activate()

    def getApplication(self):
        """Get the base application UIElement.

        If the UIElement is a child of the application, it will try
        to get the AXParent until it reaches the top application level
        element.
        """
        return self._getApplication()

    def menuItem(self, *args):
        """Return the specified menu item.

        Example - refer to items by name:

        app.menuItem('File', 'New').Press()
        app.menuItem('Edit', 'Insert', 'Line Break').Press()

        Refer to items by index:

        app.menuitem(1, 0).Press()

        Refer to items by mix-n-match:

        app.menuitem(1, 'About TextEdit').Press()
        """
        menuitem = self._getApplication().AXMenuBar
        return self._menuItem(menuitem, *args)

    def popUpItem(self, *args):
        """Return the specified item in a pop up menu."""
        self.Press()
        time.sleep(.5)
        return self._menuItem(self, *args)

    def getBundleId(self):
        """Return the bundle ID of the application."""
        return self._getBundleId()

    def getLocalizedName(self):
        """Return the localized name of the application."""
        return self._getLocalizedName()

    def sendKey(self, keychr):
        """Send one character with no modifiers."""
        return self._sendKey(keychr)

    def sendGlobalKey(self, keychr):
        """Send one character without modifiers to the system.

        It will not send an event directly to the application, system will
        dispatch it to the window which has keyboard focus.

        Parameters: keychr - Single keyboard character which will be sent.
        """
        return self._sendKey(keychr, globally=True)

    def sendKeys(self, keystr):
        """Send a series of characters with no modifiers."""
        return self._sendKeys(keystr)

    def pressModifiers(self, modifiers):
        """Hold modifier keys (e.g. [Option])."""
        return self._holdModifierKeys(modifiers)

    def releaseModifiers(self, modifiers):
        """Release modifier keys (e.g. [Option])."""
        return self._releaseModifierKeys(modifiers)

    def sendKeyWithModifiers(self, keychr, modifiers):
        """Send one character with modifiers pressed

        Parameters: key character, modifiers (list) (e.g. [SHIFT] or
                    [COMMAND, SHIFT] (assuming you've first used
                    from pyatom.AXKeyCodeConstants import *))
        """
        return self._sendKeyWithModifiers(keychr, modifiers, False)

    def sendGlobalKeyWithModifiers(self, keychr, modifiers):
        """Global send one character with modifiers pressed.

        See sendKeyWithModifiers
        """
        return self._sendKeyWithModifiers(keychr, modifiers, True)

    def dragMouseButtonLeft(self, coord, dest_coord, interval=0.5):
        """Drag the left mouse button without modifiers pressed.

        Parameters: coordinates to click on screen (tuple (x, y))
                    dest coordinates to drag to (tuple (x, y))
                    interval to send event of btn down, drag and up
        Returns: None
        """

        modFlags = 0
        self._queueMouseButton(coord, Quartz.kCGMouseButtonLeft, modFlags,
                               dest_coord=dest_coord)
        self._postQueuedEvents(interval=interval)

    def doubleClickDragMouseButtonLeft(self, coord, dest_coord, interval=0.5):
        """Double-click and drag the left mouse button without modifiers
        pressed.

        Parameters: coordinates to double-click on screen (tuple (x, y))
                    dest coordinates to drag to (tuple (x, y))
                    interval to send event of btn down, drag and up
        Returns: None
        """
        modFlags = 0
        self._queueMouseButton(coord, Quartz.kCGMouseButtonLeft, modFlags,
                               dest_coord=dest_coord)
        self._queueMouseButton(coord, Quartz.kCGMouseButtonLeft, modFlags,
                               dest_coord=dest_coord,
                               clickCount=2)
        self._postQueuedEvents(interval=interval)

    def clickMouseButtonLeft(self, coord, interval=None):
        """Click the left mouse button without modifiers pressed.

        Parameters: coordinates to click on screen (tuple (x, y))
        Returns: None
        """

        modFlags = 0
        self._queueMouseButton(coord, Quartz.kCGMouseButtonLeft, modFlags)
        if interval:
            self._postQueuedEvents(interval=interval)
        else:
            self._postQueuedEvents()

    def clickMouseButtonRight(self, coord):
        """Click the right mouse button without modifiers pressed.

        Parameters: coordinates to click on scren (tuple (x, y))
        Returns: None
        """
        modFlags = 0
        self._queueMouseButton(coord, Quartz.kCGMouseButtonRight, modFlags)
        self._postQueuedEvents()

    def clickMouseButtonLeftWithMods(self, coord, modifiers, interval=None):
        """Click the left mouse button with modifiers pressed.

        Parameters: coordinates to click; modifiers (list) (e.g. [SHIFT] or
                    [COMMAND, SHIFT] (assuming you've first used
                    from pyatom.AXKeyCodeConstants import *))
        Returns: None
        """
        modFlags = self._pressModifiers(modifiers)
        self._queueMouseButton(coord, Quartz.kCGMouseButtonLeft, modFlags)
        self._releaseModifiers(modifiers)
        if interval:
            self._postQueuedEvents(interval=interval)
        else:
            self._postQueuedEvents()

    def clickMouseButtonRightWithMods(self, coord, modifiers):
        """Click the right mouse button with modifiers pressed.

        Parameters: coordinates to click; modifiers (list)
        Returns: None
        """
        modFlags = self._pressModifiers(modifiers)
        self._queueMouseButton(coord, Quartz.kCGMouseButtonRight, modFlags)
        self._releaseModifiers(modifiers)
        self._postQueuedEvents()

    def leftMouseDragged(self, stopCoord, strCoord=(0, 0), speed=1):
        """Click the left mouse button and drag object.

        Parameters: stopCoord, the position of dragging stopped
                    strCoord, the position of dragging started
                    (0,0) will get current position
                    speed is mouse moving speed, 0 to unlimited
        Returns: None
        """
        self._leftMouseDragged(stopCoord, strCoord, speed)

    def doubleClickMouse(self, coord):
        """Double-click primary mouse button.

        Parameters: coordinates to click (assume primary is left button)
        Returns: None
        """
        modFlags = 0
        self._queueMouseButton(coord, Quartz.kCGMouseButtonLeft, modFlags)
        # This is a kludge:
        # If directed towards a Fusion VM the clickCount gets ignored and this
        # will be seen as a single click, so in sequence this will be a double-
        # click
        # Otherwise to a host app only this second one will count as a double-
        # click
        self._queueMouseButton(coord, Quartz.kCGMouseButtonLeft, modFlags,
                               clickCount=2)
        self._postQueuedEvents()

    def doubleMouseButtonLeftWithMods(self, coord, modifiers):
        """Click the left mouse button with modifiers pressed.

        Parameters: coordinates to click; modifiers (list)
        Returns: None
        """
        modFlags = self._pressModifiers(modifiers)
        self._queueMouseButton(coord, Quartz.kCGMouseButtonLeft, modFlags)
        self._queueMouseButton(coord, Quartz.kCGMouseButtonLeft, modFlags,
                               clickCount=2)
        self._releaseModifiers(modifiers)
        self._postQueuedEvents()

    def tripleClickMouse(self, coord):
        """Triple-click primary mouse button.

        Parameters: coordinates to click (assume primary is left button)
        Returns: None
        """
        # Note above re: double-clicks applies to triple-clicks
        modFlags = 0
        for i in range(2):
            self._queueMouseButton(coord, Quartz.kCGMouseButtonLeft, modFlags)
        self._queueMouseButton(coord, Quartz.kCGMouseButtonLeft, modFlags,
                               clickCount=3)
        self._postQueuedEvents()

    def waitFor(self, timeout, notification, **kwargs):
        """Generic wait for a UI event that matches the specified
        criteria to occur.

        For customization of the callback, use keyword args labeled
        'callback', 'args', and 'kwargs' for the callback fn, callback args,
        and callback kwargs, respectively.  Also note that on return,
        the observer-returned UI element will be included in the first
        argument if 'args' are given.  Note also that if the UI element is
        destroyed, callback should not use it, otherwise the function will
        hang.
        """
        return self._waitFor(timeout, notification, **kwargs)

    def waitForCreation(self, timeout=10, notification='AXCreated'):
        """Convenience method to wait for creation of some UI element.

        Returns: The element created
        """
        callback = AXCallbacks.returnElemCallback
        retelem = None
        args = (retelem, )

        return self.waitFor(timeout, notification, callback=callback,
                            args=args)

    def waitForWindowToAppear(self, winName, timeout=10):
        """Convenience method to wait for a window with the given name to
        appear.

        Returns: Boolean
        """
        return self.waitFor(timeout, 'AXWindowCreated', AXTitle=winName)

    def waitForWindowToDisappear(self, winName, timeout=10):
        """Convenience method to wait for a window with the given name to
        disappear.

        Returns: Boolean
        """
        callback = AXCallbacks.elemDisappearedCallback
        retelem = None
        args = (retelem, self)

        # For some reason for the AXUIElementDestroyed notification to fire,
        # we need to have a reference to it first
        win = self.findFirst(AXRole='AXWindow', AXTitle=winName)
        return self.waitFor(timeout, 'AXUIElementDestroyed',
                            callback=callback, args=args,
                            AXRole='AXWindow', AXTitle=winName)

    def waitForSheetToAppear(self, timeout=10):
        """Convenience method to wait for a sheet to appear.

        Returns: the sheet that appeared (element) or None
        """
        return self.waitForCreation(timeout, 'AXSheetCreated')

    def waitForValueToChange(self, timeout=10):
        """Convenience method to wait for value attribute of given element to
        change.

        Some types of elements (e.g. menu items) have their titles change,
        so this will not work for those.  This seems to work best if you set
        the notification at the application level.

        Returns: Element or None
        """
        # Want to identify that the element whose value changes matches this
        # object's.  Unique identifiers considered include role and position
        # This seems to work best if you set the notification at the application
        # level
        callback = AXCallbacks.returnElemCallback
        retelem = None
        return self.waitFor(timeout, 'AXValueChanged', callback=callback,
                            args=(retelem, ))

    def waitForFocusToChange(self, newFocusedElem, timeout=10):
        """Convenience method to wait for focused element to change (to new
        element given).

        Returns: Boolean
        """
        return self.waitFor(timeout, 'AXFocusedUIElementChanged',
                            AXRole=newFocusedElem.AXRole,
                            AXPosition=newFocusedElem.AXPosition)

    def waitForFocusedWindowToChange(self, nextWinName, timeout=10):
        """Convenience method to wait for focused window to change

        Returns: Boolean
        """
        callback = AXCallbacks.returnElemCallback
        retelem = None
        return self.waitFor(timeout, 'AXFocusedWindowChanged',
                            AXTitle=nextWinName)

    def _convenienceMatch(self, role, attr, match):
        """Method used by role based convenience functions to find a match"""
        kwargs = {}
        # If the user supplied some text to search for,
        # supply that in the kwargs
        if match:
            kwargs[attr] = match
        return self.findAll(AXRole=role, **kwargs)

    def _convenienceMatchR(self, role, attr, match):
        """Method used by role based convenience functions to find a match"""
        kwargs = {}
        # If the user supplied some text to search for,
        # supply that in the kwargs
        if match:
            kwargs[attr] = match
        return self.findAllR(AXRole=role, **kwargs)

    def textAreas(self, match=None):
        """Return a list of text areas with an optional match parameter."""
        return self._convenienceMatch('AXTextArea', 'AXTitle', match)

    def textAreasR(self, match=None):
        """Return a list of text areas with an optional match parameter."""
        return self._convenienceMatchR('AXTextArea', 'AXTitle', match)

    def textFields(self, match=None):
        """Return a list of textfields with an optional match parameter."""
        return self._convenienceMatch('AXTextField', 'AXRoleDescription', match)

    def textFieldsR(self, match=None):
        """Return a list of textfields with an optional match parameter."""
        return self._convenienceMatchR('AXTextField', 'AXRoleDescription',
                                       match)

    def buttons(self, match=None):
        """Return a list of buttons with an optional match parameter."""
        return self._convenienceMatch('AXButton', 'AXTitle', match)

    def buttonsR(self, match=None):
        """Return a list of buttons with an optional match parameter."""
        return self._convenienceMatchR('AXButton', 'AXTitle', match)

    def windows(self, match=None):
        """Return a list of windows with an optional match parameter."""
        return self._convenienceMatch('AXWindow', 'AXTitle', match)

    def windowsR(self, match=None):
        """Return a list of windows with an optional match parameter."""
        return self._convenienceMatchR('AXWindow', 'AXTitle', match)

    def sheets(self, match=None):
        """Return a list of sheets with an optional match parameter."""
        return self._convenienceMatch('AXSheet', 'AXDescription', match)

    def sheetsR(self, match=None):
        """Return a list of sheets with an optional match parameter."""
        return self._convenienceMatchR('AXSheet', 'AXDescription', match)

    def staticTexts(self, match=None):
        """Return a list of statictexts with an optional match parameter."""
        return self._convenienceMatch('AXStaticText', 'AXValue', match)

    def staticTextsR(self, match=None):
        """Return a list of statictexts with an optional match parameter"""
        return self._convenienceMatchR('AXStaticText', 'AXValue', match)

    def genericElements(self, match=None):
        """Return a list of genericelements with an optional match parameter."""
        return self._convenienceMatch('AXGenericElement', 'AXValue', match)

    def genericElementsR(self, match=None):
        """Return a list of genericelements with an optional match parameter."""
        return self._convenienceMatchR('AXGenericElement', 'AXValue', match)

    def groups(self, match=None):
        """Return a list of groups with an optional match parameter."""
        return self._convenienceMatch('AXGroup', 'AXRoleDescription', match)

    def groupsR(self, match=None):
        """Return a list of groups with an optional match parameter."""
        return self._convenienceMatchR('AXGroup', 'AXRoleDescription', match)

    def radioButtons(self, match=None):
        """Return a list of radio buttons with an optional match parameter."""
        return self._convenienceMatch('AXRadioButton', 'AXTitle', match)

    def radioButtonsR(self, match=None):
        """Return a list of radio buttons with an optional match parameter."""
        return self._convenienceMatchR('AXRadioButton', 'AXTitle', match)

    def popUpButtons(self, match=None):
        """Return a list of popup menus with an optional match parameter."""
        return self._convenienceMatch('AXPopUpButton', 'AXTitle', match)

    def popUpButtonsR(self, match=None):
        """Return a list of popup menus with an optional match parameter."""
        return self._convenienceMatchR('AXPopUpButton', 'AXTitle', match)

    def rows(self, match=None):
        """Return a list of rows with an optional match parameter."""
        return self._convenienceMatch('AXRow', 'AXTitle', match)

    def rowsR(self, match=None):
        """Return a list of rows with an optional match parameter."""
        return self._convenienceMatchR('AXRow', 'AXTitle', match)

    def sliders(self, match=None):
        """Return a list of sliders with an optional match parameter."""
        return self._convenienceMatch('AXSlider', 'AXValue', match)

    def slidersR(self, match=None):
        """Return a list of sliders with an optional match parameter."""
        return self._convenienceMatchR('AXSlider', 'AXValue', match)
